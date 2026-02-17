import torch
import torch.nn as nn
from torchvision.models import resnet18
import torch.nn.functional as F

class StrokeImageClassifier(nn.Module):
    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        self.backbone = resnet18(pretrained=pretrained)
        
        # Freeze all layers except last few
        for param in self.backbone.parameters():
            param.requires_grad = False
            
        # Unfreeze last block
        for param in self.backbone.layer4.parameters():
            param.requires_grad = True
            
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(self.backbone.fc.in_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)
