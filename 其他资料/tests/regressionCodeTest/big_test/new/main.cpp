#include <iostream>
#include <string>
#include <vector>
#include "core/image.h"
#include "filters/blur.h"
#include "filters/sharpen.h"  // New filter
#include "utils/logger.h"
#include "utils/config.h"     // New config system

void printUsage(const char* programName) {
    std::cout << "Usage: " << programName << " [options] <image_file>" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --blur <radius>    Apply blur filter with specified radius" << std::endl;
    std::cout << "  --sharpen          Apply sharpen filter" << std::endl;
    std::cout << "  --output <file>    Specify output filename" << std::endl;
    std::cout << "  --help             Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    Config::load("config.ini");
    Logger::init(Config::get("log_file", "app.log"));
    Logger::info("Image Processor v2.0 started");
    
    if (argc < 2) {
        printUsage(argv[0]);
        return 1;
    }
    
    std::string filename;
    std::string outputFile;
    bool applyBlur = false;
    bool applySharpen = false;
    int blurRadius = 3;
    
    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            printUsage(argv[0]);
            return 0;
        } else if (arg == "--blur" && i + 1 < argc) {
            applyBlur = true;
            blurRadius = std::stoi(argv[++i]);
        } else if (arg == "--sharpen") {
            applySharpen = true;
        } else if (arg == "--output" && i + 1 < argc) {
            outputFile = argv[++i];
        } else if (arg[0] != '-') {
            filename = arg;
        }
    }
    
    if (filename.empty()) {
        Logger::error("No input file specified");
        printUsage(argv[0]);
        return 1;
    }
    
    Logger::info("Loading image: " + filename);
    
    Image img;
    if (!img.load(filename)) {
        Logger::error("Failed to load image: " + filename);
        return 1;
    }
    
    // Apply filters
    if (applyBlur) {
        Logger::info("Applying blur filter with radius: " + std::to_string(blurRadius));
        BlurFilter blur(blurRadius);
        blur.apply(img);
    }
    
    if (applySharpen) {
        Logger::info("Applying sharpen filter");
        SharpenFilter sharpen;
        sharpen.apply(img);
    }
    
    // Save processed image
    if (outputFile.empty()) {
        outputFile = "output_" + filename;
    }
    
    if (img.save(outputFile)) {
        Logger::info("Image processed and saved as: " + outputFile);
    } else {
        Logger::error("Failed to save image: " + outputFile);
        return 1;
    }
    
    Logger::shutdown();
    return 0;
} 