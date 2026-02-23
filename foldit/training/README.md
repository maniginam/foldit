# Training the Garment Classifier

## Prerequisites
- Desktop/laptop with TensorFlow 2.x (`pip install tensorflow`)
- Dataset of garment images organized by category

## Dataset Structure
```
dataset/
    shirt/      (100+ images)
    pants/      (100+ images)
    towel/      (100+ images)
    small/      (100+ images)
    unknown/    (100+ images)
```

## Training
```bash
python train_model.py --data_dir ./dataset --output model.tflite --epochs 10
```

## Deploying to Raspberry Pi
Copy `model.tflite` to `/opt/foldit/model.tflite` on the Pi.
