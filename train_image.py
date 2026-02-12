#!/usr/bin/env python3
from loguru import logger
from training.image_trainer import ImageTrainer
from config import Config
Config.ensure_dirs()

if __name__ == "__main__":
    trainer = ImageTrainer(Config.IMAGES_DIR)
    cv_score = trainer.train_kfold(n_splits=5)
    logger.info(f"Final CV Score: {cv_score:.4f}")
