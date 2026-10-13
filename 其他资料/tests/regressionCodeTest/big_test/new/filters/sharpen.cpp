#include "sharpen.h"
#include <algorithm>
#include <cmath>

SharpenFilter::SharpenFilter() : strength(1.0) {
}

SharpenFilter::SharpenFilter(double s) : strength(s) {
    if (strength < 0.0) strength = 0.0;
    if (strength > 3.0) strength = 3.0;
}

void SharpenFilter::setStrength(double s) {
    strength = s;
    if (strength < 0.0) strength = 0.0;
    if (strength > 3.0) strength = 3.0;
}

double SharpenFilter::getStrength() const {
    return strength;
}

void SharpenFilter::apply(Image& image) {
    if (strength > 0.0) {
        laplacianSharpen(image);
    }
}

void SharpenFilter::unsharpMask(Image& image) {
    // Implementation of unsharp mask algorithm
    int width = image.getWidth();
    int height = image.getHeight();
    
    if (width == 0 || height == 0) return;
    
    // Create a blurred version
    Image blurred = image;
    // Simple blur for unsharp mask
    
    // Apply unsharp mask formula: original + strength * (original - blurred)
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            Pixel original = image.getPixel(x, y);
            Pixel blur = blurred.getPixel(x, y);
            
            int r = original.r + (int)(strength * (original.r - blur.r));
            int g = original.g + (int)(strength * (original.g - blur.g));
            int b = original.b + (int)(strength * (original.b - blur.b));
            
            r = std::max(0, std::min(255, r));
            g = std::max(0, std::min(255, g));
            b = std::max(0, std::min(255, b));
            
            image.setPixel(x, y, Pixel(r, g, b));
        }
    }
}

void SharpenFilter::laplacianSharpen(Image& image) {
    int width = image.getWidth();
    int height = image.getHeight();
    
    if (width == 0 || height == 0) return;
    
    Image temp(width, height);
    
    // Laplacian kernel
    int kernel[3][3] = {
        { 0, -1,  0},
        {-1,  5, -1},
        { 0, -1,  0}
    };
    
    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            double r = 0, g = 0, b = 0;
            
            for (int ky = 0; ky < 3; ky++) {
                for (int kx = 0; kx < 3; kx++) {
                    Pixel p = image.getPixel(x + kx - 1, y + ky - 1);
                    double weight = kernel[ky][kx] * strength;
                    
                    r += p.r * weight;
                    g += p.g * weight;
                    b += p.b * weight;
                }
            }
            
            // Add original pixel with reduced weight
            Pixel original = image.getPixel(x, y);
            r += original.r * (1.0 - strength);
            g += original.g * (1.0 - strength);
            b += original.b * (1.0 - strength);
            
            r = std::max(0.0, std::min(255.0, r));
            g = std::max(0.0, std::min(255.0, g));
            b = std::max(0.0, std::min(255.0, b));
            
            temp.setPixel(x, y, Pixel((unsigned char)r, (unsigned char)g, (unsigned char)b));
        }
    }
    
    // Copy result back (excluding borders)
    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            image.setPixel(x, y, temp.getPixel(x, y));
        }
    }
} 