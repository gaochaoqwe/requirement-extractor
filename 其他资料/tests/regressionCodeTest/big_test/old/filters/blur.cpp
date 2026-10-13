#include "blur.h"
#include <cmath>
#include <algorithm>

BlurFilter::BlurFilter() : radius(3) {
}

BlurFilter::BlurFilter(int r) : radius(r) {
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

void BlurFilter::apply(Image& image) {
    gaussianBlur(image);
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

double BlurFilter::gaussianWeight(int x, int y, double sigma) {
    double exponent = -(x * x + y * y) / (2.0 * sigma * sigma);
    return exp(exponent) / (2.0 * M_PI * sigma * sigma);
} 