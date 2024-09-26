import typing
from functools import partial

import torch
from ray import tune

from luna16 import (
    augmentations,
    batch_iterators,
    datasets,
    dto,
    enums,
    models,
    modules,
    services,
    trainers,
)


class LunaSegmentationLauncher:
    def __init__(
        self,
        validation_stride: int,
        num_workers: int,
        training_name: str,
        registry: services.ServiceContainer,
        training_length: int | None = None,
    ) -> None:
        self.validation_stride = validation_stride
        self.num_workers = num_workers
        self.training_name = training_name
        self.registry = registry
        self.training_length = training_length
        self.logger = registry.get_service(services.LogMessageHandler)
        self.batch_iterator = batch_iterators.BatchIteratorProvider(logger=self.logger)

    def fit(
        self,
        epochs: int,
        batch_size: int,
    ) -> dto.Scores:
        augmentation_model = augmentations.SegmentationAugmentation(
            flip=True, offset=0.03, scale=0.2, rotate=True, noise=25.0
        )
        module = modules.UNetNormalized(
            in_channels=7,
            n_classes=1,
            depth=3,
            wf=4,
            padding=True,
            batch_norm=True,
            up_mode=enums.UpMode.UP_CONV,
        )
        model = models.NoduleSegmentationModel(
            model=module,
            optimizer=torch.optim.adam.Adam(module.parameters()),
            batch_iterator=self.batch_iterator,
            logger=self.logger,
            augmentation_model=augmentation_model,
        )
        trainer = trainers.Trainer[dto.LunaSegmentationCandidate](
            name=self.training_name, logger=self.logger
        )
        train, validation = datasets.create_pre_configured_luna_segmentation(
            validation_stride=self.validation_stride,
            training_length=self.training_length,
        )
        data_module = datasets.DataModule(
            batch_size=batch_size,
            num_workers=self.num_workers,
            train=train,
            validation=validation,
        )
        return trainer.fit(model=model, epochs=epochs, data_module=data_module)

    def tune_parameters(
        self,
        epochs: int,
    ) -> tune.ResultGrid:
        hyperparameters: dict[str, typing.Any] = {
            "batch_size": tune.grid_search([16, 32, 64]),
            "learning_rate": tune.grid_search([0.0001, 0.001, 0.01]),
            "momentum": tune.grid_search([0.97, 0.98, 0.99]),
        }
        self.tunable_fit = partial(
            self.fit,
            epochs=epochs,
        )
        tuner = tune.Tuner(self.tunable_fit, param_space=hyperparameters)
        return tuner.fit()
