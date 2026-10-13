#include "image.h"
#include <iostream>
#include <fstream>
#include <algorithm>
#include <map>

// Pixel methods implementation
double Pixel::brightness() const {
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0;
}

Pixel Pixel::blend(const Pixel& other, double alpha) const {
    return Pixel(
        (unsigned char)(r * (1 - alpha) + other.r * alpha),
        (unsigned char)(g * (1 - alpha) + other.g * alpha),
        (unsigned char)(b * (1 - alpha) + other.b * alpha),
        a
    );
}

// Image class implementation
Image::Image() : width(0), height(0), metadata("") {
}

Image::Image(int w, int h) : width(w), height(h), metadata("") {
    pixels.resize(height);
    for (int i = 0; i < height; i++) {
        pixels[i].resize(width);
    }
}

Image::~Image() {
    clear();
}

bool Image::load(const std::string& filename) {
    // Enhanced image loading with metadata
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }
    
    // Simulate loading a larger image with metadata
    width = 150;  // Changed from 100
    height = 150; // Changed from 100
    metadata = "Loaded from: " + filename + ", Format: RGB";
    
    pixels.resize(height);
    
    for (int y = 0; y < height; y++) {
        pixels[y].resize(width);
        for (int x = 0; x < width; x++) {
            // Enhanced pattern generation
            pixels[y][x] = Pixel(
                (x * 2) % 255, 
                (y * 2) % 255, 
                ((x + y) * 2) % 255  // Modified pattern
            );
        }
    }
    
    file.close();
    return true;
}

bool Image::save(const std::string& filename) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }
    
    // Enhanced image saving with metadata
    file << "P6\n";
    file << "# " << metadata << "\n";  // Save metadata as comment
    file << width << " " << height << "\n255\n";
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            file.write(reinterpret_cast<const char*>(&pixels[y][x].r), 1);
            file.write(reinterpret_cast<const char*>(&pixels[y][x].g), 1);
            file.write(reinterpret_cast<const char*>(&pixels[y][x].b), 1);
        }
    }
    
    file.close();
    return true;
}

int Image::getWidth() const {
    return width;
}

int Image::getHeight() const {
    return height;
}

Pixel Image::getPixel(int x, int y) const {
    if (x >= 0 && x < width && y >= 0 && y < height) {
        return pixels[y][x];
    }
    return Pixel();
}

void Image::setPixel(int x, int y, const Pixel& pixel) {
    if (x >= 0 && x < width && y >= 0 && y < height) {
        pixels[y][x] = pixel;
    }
}

void Image::resize(int newWidth, int newHeight) {
    width = newWidth;
    height = newHeight;
    pixels.resize(height);
    for (int i = 0; i < height; i++) {
        pixels[i].resize(width);
    }
}

void Image::clear() {
    pixels.clear();
    width = 0;
    height = 0;
    metadata = "";  // Clear metadata too
}

void Image::flipHorizontal() {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width / 2; x++) {
            std::swap(pixels[y][x], pixels[y][width - 1 - x]);
        }
    }
}

void Image::flipVertical() {
    for (int y = 0; y < height / 2; y++) {
        std::swap(pixels[y], pixels[height - 1 - y]);
    }
}

// New method
void Image::rotate90() {
    std::vector<std::vector<Pixel>> rotated(width);
    for (int i = 0; i < width; i++) {
        rotated[i].resize(height);
    }
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            rotated[x][height - 1 - y] = pixels[y][x];
        }
    }
    
    pixels = rotated;
    std::swap(width, height);
}

// New advanced operations
void Image::adjustBrightness(double factor) {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            Pixel& p = pixels[y][x];
            p.r = std::min(255, (int)(p.r * factor));
            p.g = std::min(255, (int)(p.g * factor));
            p.b = std::min(255, (int)(p.b * factor));
        }
    }
}

void Image::adjustContrast(double factor) {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            Pixel& p = pixels[y][x];
            p.r = std::min(255, std::max(0, (int)((p.r - 128) * factor + 128)));
            p.g = std::min(255, std::max(0, (int)((p.g - 128) * factor + 128)));
            p.b = std::min(255, std::max(0, (int)((p.b - 128) * factor + 128)));
        }
    }
}

void Image::convertToGrayscale() {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            Pixel& p = pixels[y][x];
            unsigned char gray = (unsigned char)(p.brightness() * 255);
            p.r = p.g = p.b = gray;
        }
    }
}

Image Image::crop(int x, int y, int w, int h) const {
    Image cropped(w, h);
    for (int cy = 0; cy < h; cy++) {
        for (int cx = 0; cx < w; cx++) {
            if (x + cx < width && y + cy < height) {
                cropped.setPixel(cx, cy, getPixel(x + cx, y + cy));
            }
        }
    }
    return cropped;
}

// Metadata operations
void Image::setMetadata(const std::string& meta) {
    metadata = meta;
}

std::string Image::getMetadata() const {
    return metadata;
}

// Statistics
double Image::getAverageBrightness() const {
    double total = 0.0;
    int count = 0;
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            total += pixels[y][x].brightness();
            count++;
        }
    }
    
    return count > 0 ? total / count : 0.0;
}

Pixel Image::getDominantColor() const {
    std::map<int, int> colorCount;
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            const Pixel& p = pixels[y][x];
            int colorKey = (p.r << 16) | (p.g << 8) | p.b;
            colorCount[colorKey]++;
        }
    }
    
    int maxCount = 0;
    int dominantColor = 0;
    for (const auto& pair : colorCount) {
        if (pair.second > maxCount) {
            maxCount = pair.second;
            dominantColor = pair.first;
        }
    }
    
    return Pixel(
        (dominantColor >> 16) & 0xFF,
        (dominantColor >> 8) & 0xFF,
        dominantColor & 0xFF
    );
} 