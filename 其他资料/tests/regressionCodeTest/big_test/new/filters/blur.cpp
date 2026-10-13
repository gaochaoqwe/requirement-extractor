#include "blur.h"
#include <cmath>
#include <algorithm>

BlurFilter::BlurFilter() : radius(3), type(BLUR_GAUSSIAN), angle(0.0) {
}

BlurFilter::BlurFilter(int r) : radius(r), type(BLUR_GAUSSIAN), angle(0.0) {
    if (radius < 1) radius = 1;
    if (radius > 20) radius = 20;
}

BlurFilter::BlurFilter(int r, BlurType t) : radius(r), type(t), angle(0.0) {
    if (radius < 1) radius = 1;
    if (radius > 20) radius = 20;
}

BlurFilter::BlurFilter(int r, BlurType t, double a) : radius(r), type(t), angle(a) {
    if (radius < 1) radius = 1;
    if (radius > 20) radius = 20;
}

void BlurFilter::setRadius(int r) {
    radius = r;
    if (radius < 1) radius = 1;
    if (radius > 20) radius = 20;
}

int BlurFilter::getRadius() const {
    return radius;
}

void BlurFilter::setType(BlurType t) {
    type = t;
}

BlurType BlurFilter::getType() const {
    return type;
}

void BlurFilter::setAngle(double a) {
    angle = a;
}

double BlurFilter::getAngle() const {
    return angle;
}

void BlurFilter::apply(Image& image) {
    switch (type) {
        case BLUR_GAUSSIAN:
            gaussianBlur(image);
            break;
        case BLUR_BOX:
            boxBlur(image);
            break;
        case BLUR_MOTION:
            motionBlur(image);
            break;
        default:
            gaussianBlur(image);
            break;
    }
}

void BlurFilter::gaussianBlur(Image& image) {
    int width = image.getWidth();
    int height = image.getHeight();
    
    if (width == 0 || height == 0) return;
    
    Image temp(width, height);
    double sigma = radius / 3.0;
    
    // Apply horizontal blur
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            double totalR = 0, totalG = 0, totalB = 0;
            double totalWeight = 0;
            
            for (int i = -radius; i <= radius; i++) {
                int srcX = x + i;
                if (srcX >= 0 && srcX < width) {
                    Pixel p = image.getPixel(srcX, y);
                    double weight = gaussianWeight(i, 0, sigma);
                    
                    totalR += p.r * weight;
                    totalG += p.g * weight;
                    totalB += p.b * weight;
                    totalWeight += weight;
                }
            }
            
            if (totalWeight > 0) {
                Pixel blurred(
                    (unsigned char)(totalR / totalWeight),
                    (unsigned char)(totalG / totalWeight),
                    (unsigned char)(totalB / totalWeight)
                );
                temp.setPixel(x, y, blurred);
            }
        }
    }
    
    // Apply vertical blur
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            double totalR = 0, totalG = 0, totalB = 0;
            double totalWeight = 0;
            
            for (int i = -radius; i <= radius; i++) {
                int srcY = y + i;
                if (srcY >= 0 && srcY < height) {
                    Pixel p = temp.getPixel(x, srcY);
                    double weight = gaussianWeight(0, i, sigma);
                    
                    totalR += p.r * weight;
                    totalG += p.g * weight;
                    totalB += p.b * weight;
                    totalWeight += weight;
                }
            }
            
            if (totalWeight > 0) {
                Pixel blurred(
                    (unsigned char)(totalR / totalWeight),
                    (unsigned char)(totalG / totalWeight),
                    (unsigned char)(totalB / totalWeight)
                );
                image.setPixel(x, y, blurred);
            }
        }
    }
}

void BlurFilter::boxBlur(Image& image) {
    int width = image.getWidth();
    int height = image.getHeight();
    
    if (width == 0 || height == 0) return;
    
    Image temp(width, height);
    
    // Apply horizontal blur
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int totalR = 0, totalG = 0, totalB = 0;
            int count = 0;
            
            for (int i = -radius; i <= radius; i++) {
                int srcX = x + i;
                if (srcX >= 0 && srcX < width) {
                    Pixel p = image.getPixel(srcX, y);
                    totalR += p.r;
                    totalG += p.g;
                    totalB += p.b;
                    count++;
                }
            }
            
            if (count > 0) {
                Pixel blurred(
                    (unsigned char)(totalR / count),
                    (unsigned char)(totalG / count),
                    (unsigned char)(totalB / count)
                );
                temp.setPixel(x, y, blurred);
            }
        }
    }
    
    // Apply vertical blur
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int totalR = 0, totalG = 0, totalB = 0;
            int count = 0;
            
            for (int i = -radius; i <= radius; i++) {
                int srcY = y + i;
                if (srcY >= 0 && srcY < height) {
                    Pixel p = temp.getPixel(x, srcY);
                    totalR += p.r;
                    totalG += p.g;
                    totalB += p.b;
                    count++;
                }
            }
            
            if (count > 0) {
                Pixel blurred(
                    (unsigned char)(totalR / count),
                    (unsigned char)(totalG / count),
                    (unsigned char)(totalB / count)
                );
                image.setPixel(x, y, blurred);
            }
        }
    }
}

void BlurFilter::motionBlur(Image& image) {
    int width = image.getWidth();
    int height = image.getHeight();
    
    if (width == 0 || height == 0) return;
    
    Image temp(width, height);
    
    double cosAngle = cos(angle);
    double sinAngle = sin(angle);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            double totalR = 0, totalG = 0, totalB = 0;
            int count = 0;
            
            for (int i = -radius; i <= radius; i++) {
                int srcX = x + (int)(i * cosAngle);
                int srcY = y + (int)(i * sinAngle);
                
                if (srcX >= 0 && srcX < width && srcY >= 0 && srcY < height) {
                    Pixel p = image.getPixel(srcX, srcY);
                    totalR += p.r;
                    totalG += p.g;
                    totalB += p.b;
                    count++;
                }
            }
            
            if (count > 0) {
                Pixel blurred(
                    (unsigned char)(totalR / count),
                    (unsigned char)(totalG / count),
                    (unsigned char)(totalB / count)
                );
                temp.setPixel(x, y, blurred);
            } else {
                temp.setPixel(x, y, image.getPixel(x, y));
            }
        }
    }
    
    // Copy result back
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            image.setPixel(x, y, temp.getPixel(x, y));
        }
    }
}

double BlurFilter::gaussianWeight(int x, int y, double sigma) {
    double exponent = -(x * x + y * y) / (2.0 * sigma * sigma);
    return exp(exponent) / (2.0 * M_PI * sigma * sigma);
} 