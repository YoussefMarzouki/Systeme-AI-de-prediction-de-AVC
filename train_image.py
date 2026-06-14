#!/usr/bin/env python3
"""Entry point for MRI image-model training."""

import argparse
import json

from loguru import logger

from config import Config
from training.image_trainer import ImageTrainer


def parse_args():
    parser = argparse.ArgumentParser(description="Train MRI image model")
    parser.add_argument(
        "--images-dir",
        type=str,
        default=str(Config.IMAGE_DATASET_DIR),
        help="Path to class-organized MRI images directory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    Config.ensure_dirs()

    logger.info("=== Training Configuration ===")
    for key, value in Config.get_config_summary().items():
        logger.info(f"{key}: {value}")
    logger.info(f"images_dir: {args.images_dir}")

    trainer = ImageTrainer(images_dir=args.images_dir)
    test_f1 = trainer.train()

    summary = {
        "final_f1_score": float(test_f1),
        "epochs": Config.EPOCHS,
        "learning_rate": Config.LR,
        "batch_size": Config.BATCH_SIZE,
        "training_completed": True,
        "image_model_path": str(Config.IMAGE_MODEL_PATH),
    }
    summary_path = Config.MODELS_DIR / "final_training_config.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    logger.info("=== Training Complete ===")
    logger.info("Test F1 Score: {:.4f}", test_f1)
    logger.info("Summary saved to: {}", summary_path)


if __name__ == "__main__":
    main()
