cmake_minimum_required(VERSION 3.8)
project(ad_r1m_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(xacro REQUIRED)

# Option to skip downloading third-party models (for CI or offline builds)
option(DOWNLOAD_GAZEBO_MODELS "Download third-party Gazebo models" ON)

if(DOWNLOAD_GAZEBO_MODELS)

include(ExternalProject)

# Download third-party Gazebo models at build time
# Sources:
#   OSRF Gazebo Models (CC BY 3.0):   https://github.com/osrf/gazebo_models
#   OSRF ARIAC (Apache 2.0):          https://bitbucket.org/osrf/ariac
#   OSRF ServiceSim (Apache 2.0):     https://github.com/osrf/servicesim

set(MODELS_INSTALL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/models)
set(WORLDS_INSTALL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/worlds)

# Models from OSRF gazebo_models - for factory world
set(GAZEBO_MODEL_LIST
  arm_part
  coke_can
  construction_barrel
  construction_cone
  control_console
  cordless_drill
  disk_part
  dumpster
  euro_pallet
  first_2015_trash_can
  grey_wall
  plastic_cup
  ground_plane
  sun
  table
  tube_2_25cm
)

# Models from OSRF ARIAC - for factory world
set(ARIAC_MODEL_LIST
  workcell
  workcell_bin
  shipping_container_ariac
)

# Models from OSRF ServiceSim - for aws_office world
set(SERVICESIM_MODEL_LIST
  actor
  bathroom_sink
  cafe_counter
  casual_female
  coffee_maker
  computer
  conference_table_large
  conference_table_small
  cubicle_corner
  cubicle_island
  cubicle_wall
  desk
  desk_chair
  dishwasher
  elegant_female
  elegant_female2
  elegant_male
  hangout_chair
  microwave
  mini_fridge
  office_box
  office_cafe_table
  office_chair
  office_couch
  office_desk
  office_lamp
  office_table
  reception_desk
  refrigerator
  servicebot
  toilet
  tv_stand
  wastebasket
  whiteboard
)

# Build copy commands for each source
set(GAZEBO_COPY_COMMANDS "")
foreach(MODEL ${GAZEBO_MODEL_LIST})
  list(APPEND GAZEBO_COPY_COMMANDS
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      <SOURCE_DIR>/${MODEL}
      ${MODELS_INSTALL_DIR}/${MODEL}
  )
endforeach()

set(ARIAC_COPY_COMMANDS "")
foreach(MODEL ${ARIAC_MODEL_LIST})
  list(APPEND ARIAC_COPY_COMMANDS
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      <SOURCE_DIR>/osrf_gear/models/${MODEL}
      ${MODELS_INSTALL_DIR}/${MODEL}
  )
endforeach()

set(SERVICESIM_COPY_COMMANDS "")
foreach(MODEL ${SERVICESIM_MODEL_LIST})
  list(APPEND SERVICESIM_COPY_COMMANDS
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      <SOURCE_DIR>/servicesim_competition/models/${MODEL}
      ${MODELS_INSTALL_DIR}/${MODEL}
  )
endforeach()

# OSRF Gazebo Models (CC BY 3.0) - download only, no build
ExternalProject_Add(gazebo_models
  GIT_REPOSITORY https://github.com/osrf/gazebo_models.git
  GIT_TAG master
  GIT_SHALLOW TRUE
  GIT_PROGRESS FALSE
  LOG_DOWNLOAD TRUE
  LOG_UPDATE TRUE
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${GAZEBO_COPY_COMMANDS}
)

# OSRF ARIAC (Apache 2.0) - download only, no build
ExternalProject_Add(ariac_models
  GIT_REPOSITORY https://bitbucket.org/osrf/ariac.git
  GIT_TAG master
  GIT_SHALLOW TRUE
  GIT_PROGRESS FALSE
  LOG_DOWNLOAD TRUE
  LOG_UPDATE TRUE
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${ARIAC_COPY_COMMANDS}
)

# OSRF ServiceSim (Apache 2.0) - download only, no build
ExternalProject_Add(servicesim_models
  GIT_REPOSITORY https://github.com/osrf/servicesim.git
  GIT_TAG master
  GIT_SHALLOW TRUE
  GIT_PROGRESS FALSE
  LOG_DOWNLOAD TRUE
  LOG_UPDATE TRUE
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND
    ${SERVICESIM_COPY_COMMANDS}
    COMMAND ${CMAKE_COMMAND} -E copy_directory
      <SOURCE_DIR>/servicesim_competition/media
      ${WORLDS_INSTALL_DIR}/media
)

endif() # DOWNLOAD_GAZEBO_MODELS

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Install directories
install(
  DIRECTORY config launch urdf worlds models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
