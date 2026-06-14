import torch
import torch.nn as nn
from torchvision.models import (
    ResNet18_Weights,
    ResNet50_Weights,
    resnet18,
    resnet50,
)


class StrokeImageClassifier(nn.Module):
    def __init__(self, num_classes=2, pretrained=True, backbone="resnet18", freeze_strategy="partial"):
        super().__init__()
        self.num_classes = int(num_classes)
        self.backbone_name = backbone
        self.freeze_strategy = freeze_strategy

        # Load backbone model
        if backbone == "resnet18":
            weights = ResNet18_Weights.DEFAULT if pretrained else None
            self.backbone = resnet18(weights=weights)
            in_features = 512
        elif backbone == "resnet50":
            weights = ResNet50_Weights.DEFAULT if pretrained else None
            self.backbone = resnet50(weights=weights)
            in_features = 2048
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")

        # Apply freeze strategy
        self._apply_freeze_strategy(freeze_strategy)

        # Replace classification head
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, self.num_classes)
        )

    def _apply_freeze_strategy(self, strategy):
        """Apply different freeze strategies to the backbone."""
        if strategy == "full":
            # Freeze all layers
            for param in self.backbone.parameters():
                param.requires_grad = False
        elif strategy == "partial":
            # Freeze all layers except last block
            for param in self.backbone.parameters():
                param.requires_grad = False
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True
        elif strategy == "gradual":
            # Gradual unfreezing: only freeze early layers
            # Freeze layer1 and layer2, unfreeze layer3 and layer4
            for param in self.backbone.layer1.parameters():
                param.requires_grad = False
            for param in self.backbone.layer2.parameters():
                param.requires_grad = False
            for param in self.backbone.layer3.parameters():
                param.requires_grad = True
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True
        elif strategy == "none":
            # Unfreeze all layers
            for param in self.backbone.parameters():
                param.requires_grad = True
        else:
            raise ValueError(f"Unsupported freeze strategy: {strategy}")

    def get_backbone_parameters(self):
        backbone_params = []
        classifier_params = []

        for name, param in self.backbone.named_parameters():
            if name.startswith("fc."):
                classifier_params.append(param)
            else:
                backbone_params.append(param)

        return backbone_params, classifier_params

    def gradual_unfreeze(self, current_epoch, total_epochs):
        if self.freeze_strategy != "gradual":
            return

        # Start with only late blocks trainable, then unfreeze earlier blocks over time.
        progress = float(current_epoch + 1) / float(max(total_epochs, 1))
        if progress >= 0.66:
            for param in self.backbone.layer2.parameters():
                param.requires_grad = True
        if progress >= 0.85:
            for param in self.backbone.layer1.parameters():
                param.requires_grad = True

    def forward(self, x):
        return self.backbone(x)
