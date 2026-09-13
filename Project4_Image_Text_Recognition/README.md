# 🤖 AI Image & Text Recognition System

## 📌 Project Overview

This project is an interactive image and text recognition application developed as part of my **Artificial Intelligence Internship at DecodeLabs**.

The application uses Optical Character Recognition (OCR) to extract readable text from uploaded images. Image preprocessing techniques are applied before recognition to improve the input provided to the OCR engine.

## 🎯 Objective

The objective of this project is to build a basic image/text recognition system that:

- Accepts an image as input
- Preprocesses the image
- Performs text recognition using an OCR library
- Displays the recognized text
- Provides basic recognition statistics

## ⚙️ Processing Pipeline

```text
Image Upload
     ↓
Grayscale Conversion
     ↓
Gaussian Blur
     ↓
Thresholding
     ↓
OCR Recognition
     ↓
Extracted Text