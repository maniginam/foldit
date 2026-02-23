"""MobileNetV2 fine-tuning for garment classification."""
import os
import sys


def train(csv_path, output_dir="models", epochs=20, batch_size=16):
    """Fine-tune MobileNetV2 on labeled garment data."""
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow not installed. Install with: pip install tensorflow>=2.15.0")
        sys.exit(1)

    from training.dataset import DatasetSplitter

    splitter = DatasetSplitter(csv_path)
    train_rows, val_rows, _ = splitter.split()

    if not train_rows:
        print("No training data found.")
        return None

    train_images, train_labels = splitter.load_images(train_rows, size=(224, 224))
    val_images, val_labels = splitter.load_images(val_rows, size=(224, 224))

    label_set = sorted(set(train_labels))
    label_to_idx = {l: i for i, l in enumerate(label_set)}
    train_y = tf.keras.utils.to_categorical([label_to_idx[l] for l in train_labels], len(label_set))
    val_y = tf.keras.utils.to_categorical([label_to_idx[l] for l in val_labels], len(label_set))

    train_x = tf.keras.applications.mobilenet_v2.preprocess_input(train_images.astype("float32"))
    val_x = tf.keras.applications.mobilenet_v2.preprocess_input(val_images.astype("float32"))

    base = tf.keras.applications.MobileNetV2(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    base.trainable = False

    model = tf.keras.Sequential([
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(len(label_set), activation="softmax"),
    ])

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5),
    ]

    model.fit(train_x, train_y, validation_data=(val_x, val_y),
              epochs=epochs, batch_size=batch_size, callbacks=callbacks)

    os.makedirs(output_dir, exist_ok=True)
    h5_path = os.path.join(output_dir, "garment_classifier.h5")
    model.save(h5_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    tflite_path = os.path.join(output_dir, "garment_classifier.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    label_path = os.path.join(output_dir, "labels.txt")
    with open(label_path, "w") as f:
        for label in label_set:
            f.write(label + "\n")

    print(f"Model saved to {h5_path}")
    print(f"TFLite model saved to {tflite_path}")
    print(f"Labels saved to {label_path}")
    return tflite_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train garment classifier")
    parser.add_argument("--csv", required=True, help="Path to labels.csv")
    parser.add_argument("--output", default="models", help="Output directory")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    train(args.csv, args.output, args.epochs)
