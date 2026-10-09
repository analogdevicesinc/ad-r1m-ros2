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

# -- lift_waypoint_demo --
install(
  DIRECTORY lift_waypoint_demo/launch
  DESTINATION share/${PROJECT_NAME}/lift_waypoint_demo
)

install(PROGRAMS
  lift_waypoint_demo/scripts/commander/demo_run.py
  lift_waypoint_demo/scripts/commander/elevator_server.py
  lift_waypoint_demo/scripts/waypoint_follower.py
  lift_waypoint_demo/scripts/velocity_control.py
  DESTINATION lib/${PROJECT_NAME}
)

# -- imu_hil_demo --
install(
  DIRECTORY imu_hil_demo/launch imu_hil_demo/config
  DESTINATION share/${PROJECT_NAME}/imu_hil_demo
)

install(PROGRAMS
  imu_hil_demo/scripts/imu_hil_controller.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
