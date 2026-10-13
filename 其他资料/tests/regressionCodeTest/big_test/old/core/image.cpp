#include "image.h"
#include <iostream>
#include <fstream>

Image::Image() : width(0), height(0) {
}

Image::Image(int w, int h) : width(w), height(h) {
    pixels.resize(height);
    for (int i = 0; i < height; i++) {
        pixels[i].resize(width);
    }
}

Image::~Image() {
    clear();
}

bool Image::load(const std::string& filename) {
    // Simplified image loading (just simulate)
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }
    
    // Simulate loading a 100x100 image
    width = 100;
    height = 100;
    pixels.resize(height);
    
    for (int y = 0; y < height; y++) {
        pixels[y].resize(width);
        for (int x = 0; x < width; x++) {
            // Generate some pattern
            pixels[y][x] = Pixel(x * 2, y * 2, (x + y) % 255);
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
    
    // Simplified image saving
    file << "P6\n" << width << " " << height << "\n255\n";
    
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