import typer

from luna16 import bootstrap, data_processing, settings, training

cli = typer.Typer()


@cli.command(name="create_cutouts")
def create_cutouts(training_length: int | None = None) -> None:
    # If num workers is greated than 0, run in parallel
    cutout_service = data_processing.CtCutoutService()
    if settings.NUM_WORKERS:
        cutout_service.create_cutouts_concurrent(training_length=training_length)
    # Otherwise, run sequentially
    else:
        cutout_service.create_cutouts(training_length=training_length)


@cli.command(name="train_luna_classification")
def train_luna_classification(
    version: str,
    epochs: int = 1,
    batch_size: int = 32,
    validation_stride: int = 5,
    profile: bool = False,
) -> None:
    training_name = "Classification"
    registry = bootstrap.create_registry()
    training.LunaClassificationLauncher(
        registry=registry,
        validation_stride=validation_stride,
        training_name=training_name,
        validation_cadence=5,
    ).fit(
        epochs=epochs,
        batch_size=batch_size,
        lr=0.001,
        momentum=0.99,
        conv_channels=8,
        profile=profile,
        version=version,
    )
    registry.close_all_services()


@cli.command(name="tune_luna_classification")
def tune_luna_classification(
    epochs: int = 1,
    validation_stride: int = 5,
) -> None:
    training_name = "Classification"
    registry = bootstrap.create_registry()
    training.LunaClassificationLauncher(
        registry=registry,
        validation_stride=validation_stride,
        training_name=training_name,
        validation_cadence=5,
    ).tune_parameters(epochs=epochs)
    registry.close_all_services()


@cli.command(name="train_luna_malignant_classification")
def train_luna_malignant_classification(
    version: str,
    state_name: str,
    state_version: str,
    epochs: int = 1,
    batch_size: int = 32,
    validation_stride: int = 5,
) -> None:
    training_name = "Malignant Classification"
    registry = bootstrap.create_registry()
    training.LunaMalignantClassificationLauncher(
        registry=registry,
        validation_stride=validation_stride,
        state_name=state_name,
        state_version=state_version,
        training_name=training_name,
    ).fit(
        epochs=epochs,
        batch_size=batch_size,
        version=version,
    )
    registry.close_all_services()


if __name__ == "__main__":
    cli()
