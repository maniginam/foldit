"""Training script for garment classification model.

Run on a desktop/laptop with TensorFlow installed (not on RPi).

Usage:
    python train_model.py --data_dir ./dataset --output model.tflite
"""
import argparse


def create_parser():
    parser = argparse.ArgumentParser(description="Train garment classifier")
    parser.add_argument("--data_dir", required=True, help="Path to dataset directory")
    parser.add_argument("--output", default="model.tflite", help="Output .tflite file")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    return parser


def train(data_dir, output_path, epochs, batch_size):
    try:
        import tensorflow as tf
    except ImportError:
        print("ERROR: TensorFlow required. Install with: pip install tensorflow")
        print("This script runs on desktop/laptop, NOT on Raspberry Pi.")
        return

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3), include_top=False, weights="imagenet"
    )
    base_model.trainable = False

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(5, activation="softmax")
    ])

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0/255, validation_split=0.2, horizontal_flip=True, rotation_range=15
    )
    train_gen = datagen.flow_from_directory(
        data_dir, target_size=(224, 224), batch_size=batch_size,
        class_mode="categorical", subset="training"
    )
    val_gen = datagen.flow_from_directory(
        data_dir, target_size=(224, 224), batch_size=batch_size,
        class_mode="categorical", subset="validation"
    )

    model.fit(train_gen, validation_data=val_gen, epochs=epochs)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_model)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    train(args.data_dir, args.output, args.epochs, args.batch_size)
