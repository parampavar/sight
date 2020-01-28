<p align="center">
    <br>
	<img src="https://github.com/rish-16/sight/blob/master/Assets/logo.png?raw=true" width=200>
    <br>
<p>

<p align="center">
    <a href="https://github.com/rish-16/sight/blob/master/LICENSE">
		<img alt="AUR license" src="https://img.shields.io/badge/License-Apache%202.0-yellow.svg">
    </a>
</p>

<h3 align="center">
<p>State-of-the-art Computer Vision and Object Detection for TensorFlow.</p>
</h3>

*sightseer* provides state-of-the-art general-purpose architectures (YOLOv3, MaskRCNN, Fast/Faster RCNN, SSD...) for Computer Vision and Object Detection tasks with 30+ pretrained models written in TensorFlow 1.15.

## Installation

`sightseer` is written in Python 3.5+ and TensorFlow 1.15. 

Ideally, `sightseer` should be installed in a [virtual environments](https://docs.python.org/3/library/venv.html). If you're unfamiliar with Python virtual environments, check out this [tutorial](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) on getting started.

### Via PyPi

To use `sightseer`, you must first have TensorFlow installed. To do so, follow the instructions on the [TensorFlow installation page](https://www.tensorflow.org/install/pip?lang=python3).

When your virtual environment is set up with TensorFlow, you can install `sightseer` using `pip`:

```bash
pip install sightseer
```

### Model Architectures (as of now)

1. YOLOv3 (Darknet by Joseph Redmon)

> Facebook AI's *Mask R-CNN* will be out in the v1.1.0 release. For more information on model release, check out the [Roadmap](https://github.com/rish-16/sight/blob/master/ROADMAP.md).


# Components of `sightseer`

The package comes with 4 major components that help with different parts of the object detection process all the way from preparing your raw data to getting predictions and displaying them.

| Component | Description                                                               |
|-----------|---------------------------------------------------------------------------|
| Sightseer | Obtains image data or video footage                                       |
| Proc      | Provides image/frame-wise annotation and inter-format conversion tools    |
| Zoo       | Stores the wrappers over all state-of-the-art models and configs          |
| Serve     | Provides deployment and model serving protocols and services              |

If not using custom datasets, `Sightseer` and `Zoo` are the submodules majorly used for generic predictions from pre-trained models. When there is custom data involved, you can use `Proc` to annotate your datasets and even convert them between XML/JSON/CSV/TFRecord formats. 

> `Serve` is an experimental productionising submodule that helps deploy your models on cloud services like AWS and GCP. For more details on future tools and services, check out the [Roadmap](https://github.com/rish-16/sight/blob/master/ROADMAP.md).

## Features

<strong>1. Loading images</strong>

Footage or raw images can be rendered using `Sightseer` before being ingested into models or further preprocessed.

```python
from sightseer import Sightseer

ss = Sightseer()
image = ss.load_image("path/to/image")
```

> Support for video, webcam footage, and screen recording will be out in the coming v1.1.0 release.

<strong>2. Using models from `sightseer.zoo`</strong>

Once installed, any model offered by `sightseer` can be accessed in less than 10 lines of code. For instance, the code to use the YOLOv3 (Darknet) model is as follows:

```python
from sightseer import Sightseer
from sightseer.zoo import YOLOv3Client
from pprint import pprint

yolo = YOLOv3Client()
yolo.load_model() # downloads weights

# loading image from local system
ss = Sightseer()
image = ss.load_image("./images/road.jpg")

# getting labels, confidence scores, and bounding box data
preds, pred_img = yolo.predict(image, return_img=True)
pprint (preds)
ss.render_image(pred_img)
```

This can even be converted into a Command-line Interface (CLI) using arguments from `argparse`.

## Contributing

Suggestions, improvements, and enhancements are always welcome! If you have any issues, please do raise one in the Issues section. If you have an improvement, do file an issue to discuss the suggestion before creating a PR.

All ideas – no matter how outrageous – welcome!

## Licence

[Apache Licencse 2.0](https://github.com/rish-16/sight/blob/master/LICENSE)