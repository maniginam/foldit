"""Validate a TFLite garment classifier model."""
import sys


def validate(tflite_path, csv_path, labels_path):
    """Run validation on test split and report per-class metrics."""
    try:
        import numpy as np
    except ImportError:
        print("NumPy not installed.")
        sys.exit(1)

    from training.dataset import DatasetSplitter

    splitter = DatasetSplitter(csv_path)
    _, _, test_rows = splitter.split()

    if not test_rows:
        print("No test data found.")
        return None

    test_images, test_labels = splitter.load_images(test_rows, size=(224, 224))

    with open(labels_path, "r") as f:
        label_set = [line.strip() for line in f if line.strip()]

    try:
        import tflite_runtime.interpreter as tflite
        interpreter = tflite.Interpreter(model_path=tflite_path)
    except ImportError:
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=tflite_path)

    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    predictions = []
    for img in test_images:
        input_data = np.expand_dims(img.astype(np.float32), axis=0)
        interpreter.set_tensor(input_details[0]["index"], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])
        predictions.append(label_set[np.argmax(output[0])])

    report = {}
    for label in label_set:
        tp = sum(1 for p, t in zip(predictions, test_labels) if p == label and t == label)
        fp = sum(1 for p, t in zip(predictions, test_labels) if p == label and t != label)
        fn = sum(1 for p, t in zip(predictions, test_labels) if p != label and t == label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        report[label] = {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "fn": fn}

    accuracy = sum(1 for p, t in zip(predictions, test_labels) if p == t) / len(test_labels)
    return {"accuracy": accuracy, "per_class": report}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate garment classifier")
    parser.add_argument("--model", required=True, help="Path to .tflite model")
    parser.add_argument("--csv", required=True, help="Path to labels.csv")
    parser.add_argument("--labels", required=True, help="Path to labels.txt")
    args = parser.parse_args()
    result = validate(args.model, args.csv, args.labels)
    if result:
        print(f"Accuracy: {result['accuracy']:.1%}")
        for cls, metrics in result["per_class"].items():
            flag = " ⚠️" if metrics["recall"] < 0.8 else ""
            print(f"  {cls}: precision={metrics['precision']:.1%} recall={metrics['recall']:.1%}{flag}")
