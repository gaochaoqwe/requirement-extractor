#include <string>

int unchangedProbe(const std::string& input) {
  int sum = 0;
  for (char c : input) {
    sum += static_cast<unsigned char>(c);
  }
  return sum;
}
