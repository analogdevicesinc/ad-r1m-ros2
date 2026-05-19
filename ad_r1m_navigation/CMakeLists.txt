cmake_minimum_required(VERSION 3.8)
project(ad_r1m_navigation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Install directories
install(
  DIRECTORY config launch maps
  DESTINATION share/${PROJECT_NAME}
)
 
# Install Python scripts
install(PROGRAMS 
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
