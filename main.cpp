/**
 * This is the outline of the program. When judging on the online judger, we will provide this file.
 * So you don't have to submit it.
 *
 * If you want to use our visualizer for better output, don't modify this program unless you fully understands it.
 * (But it's quite simple!)
 *
 * NOTE: Our final judger won't look like the one we provide you with, so...... don't try to hack it.
 */
#include <chrono>
#include <iostream>

#include "game_of_life.h"

/**
 * Test function if you want to test the overall performance of your program.
 * Everyone must pass this test on OJ to check the correctness of your program.
 */
void VisualizeTest() {
  Initialize();
  int round = 0;
  std::cin >> round;
  PrintGame();
  std::cout << 0 << " " << GetLiveCell() << std::endl;
  for (int i = 1; i <= round; ++i) {
    Tick();
    PrintGame();
    std::cout << i << " " << GetLiveCell() << std::endl;
  }
}

/**
 * Test function if you want to test the efficiency of your program.
 * For students in class A, you MUST pass this part of test on OJ.
 * For students in class B, we strongly recommend you to give it a try (or at least think about it).
 */
void PressureTest() {
  auto start_point = std::chrono::high_resolution_clock::now();
  Initialize();
  int round = 0;
  std::cin >> round;
  int time_limit = 0;
  std::cin >> time_limit;
  for (int i = 0; i < round; ++i) {
    Tick();
  }
  auto end_point = std::chrono::high_resolution_clock::now();
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_point - start_point);
  if (duration > std::chrono::milliseconds(time_limit)) {
    std::cerr << "Time Limit Exceeded. Try to make your program faster to pass this test. :(" << std::endl;
    exit(-1);
  } else {
    std::cout << "You pass this test. Congratulations! :)" << std::endl;
  }
}

int main() {
  // VisualizeTest();
  PressureTest();
  return 0;
}
