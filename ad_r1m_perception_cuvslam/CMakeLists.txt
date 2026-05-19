cmake_minimum_required(VERSION 3.8)
project(ad_r1m_perception_cuvslam)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)

# add_library() instead of add_executable for composable nodes
add_library(realsense_image_sync_component SHARED src/realsense_image_sync.cpp)
ament_target_dependencies(realsense_image_sync_component rclcpp rclcpp_components sensor_msgs)
rclcpp_components_register_node(
  realsense_image_sync_component
  PLUGIN "camera_sync::MultiApproxSync"
  EXECUTABLE realsense_image_sync
)

install(TARGETS realsense_image_sync_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY
	launch config urdf meshes worlds
	DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
