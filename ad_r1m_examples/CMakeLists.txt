cmake_minimum_required(VERSION 3.8)
project(ad_r1m_examples)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Install directories
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Install Python scripts
install(PROGRAMS
  scripts/commander/demo_run.py
  scripts/commander/elevator_server.py
  # scripts/commander/waypoint_follower.py
  scripts/waypoint_follower.py
  scripts/velocity_control.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
