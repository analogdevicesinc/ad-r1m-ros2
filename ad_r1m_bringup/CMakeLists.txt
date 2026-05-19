cmake_minimum_required(VERSION 3.8)
project(ad_r1m_bringup)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(lely_core_libraries REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# Generate DCF files for the CANopen nodes
cogen_dcf(canopen)

# Install directories
install(
  DIRECTORY config launch urdf
  DESTINATION share/${PROJECT_NAME}
  PATTERN "bus.yml" EXCLUDE
)
 
# Install Python scripts
install(PROGRAMS 
  scripts/crsf/crsf_node.py
  scripts/crsf/teleop_keyboard.py
  scripts/adrd_bms/adrd_bms_node.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
