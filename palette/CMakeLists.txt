cmake_minimum_required(VERSION 3.20)
project(Safe_BIM_Palette LANGUAGES C CXX)

set(AC_API_DEVKIT_DIR "" CACHE PATH "Archicad 29 API Development Kit")
if(NOT EXISTS "${AC_API_DEVKIT_DIR}/Support/Inc/ACAPinc.h")
  message(FATAL_ERROR "Set AC_API_DEVKIT_DIR to the Archicad 29 API Development Kit")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_definitions(-DUNICODE -D_UNICODE -D_ITERATOR_DEBUG_LEVEL=0 -DGS_WIN -DACExtension)

file(GLOB PALETTE_SOURCES Src/*.cpp Src/*.c Src/*.hpp Src/*.h)
set_source_files_properties(Src/APICommon.c PROPERTIES LANGUAGE CXX)
add_library(AddOn SHARED ${PALETTE_SOURCES})
set_target_properties(AddOn PROPERTIES OUTPUT_NAME Safe_BIM_Palette SUFFIX ".apx")
target_include_directories(AddOn PRIVATE Src "${AC_API_DEVKIT_DIR}/Support/Inc")
target_link_libraries(AddOn PRIVATE "${AC_API_DEVKIT_DIR}/Support/Lib/ACAP_STAT.lib")
target_compile_options(AddOn PRIVATE /W3 /WX /wd4996 /Zc:wchar_t-)

file(GLOB GS_INCLUDE_FOLDERS "${AC_API_DEVKIT_DIR}/Support/Modules/*")
foreach(folder ${GS_INCLUDE_FOLDERS})
  target_include_directories(AddOn PRIVATE "${folder}")
  file(GLOB module_libs "${folder}/Win/*.lib")
  target_link_libraries(AddOn PRIVATE ${module_libs})
endforeach()

get_filename_component(GSNEW "${AC_API_DEVKIT_DIR}/Support/Modules/GSRoot/GSNew.hpp" REALPATH)
get_filename_component(GSMALLOC "${AC_API_DEVKIT_DIR}/Support/Modules/GSRoot/GSMalloc.hpp" REALPATH)
target_compile_options(AddOn PRIVATE "SHELL:/FI \"${GSNEW}\"" "SHELL:/FI \"${GSMALLOC}\"")

set(RESOURCE_DIR "${CMAKE_BINARY_DIR}/ResourceObjects")
set(RESOURCE_FILE "${RESOURCE_DIR}/Safe_BIM_Palette.res")
add_custom_command(
  OUTPUT "${RESOURCE_DIR}/resources.stamp"
  COMMAND ${CMAKE_COMMAND} -E make_directory "${RESOURCE_DIR}"
  COMMAND ${Python3_EXECUTABLE}
    "${AC_API_DEVKIT_DIR}/Support/Tools/CompileResources.py"
    INT "${AC_API_DEVKIT_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}/Src"
    "${CMAKE_CURRENT_SOURCE_DIR}" "${RESOURCE_DIR}" "${RESOURCE_FILE}"
  COMMAND ${CMAKE_COMMAND} -E touch "${RESOURCE_DIR}/resources.stamp"
  DEPENDS RFIX/Safe_BIM_Palette.grc RFIX/Safe_BIM_Palette.html RFIX.win/Safe_BIM_Palette.rc2
)
add_custom_target(AddOnResources ALL DEPENDS "${RESOURCE_DIR}/resources.stamp")
add_dependencies(AddOn AddOnResources)
target_link_options(AddOn PRIVATE "${RESOURCE_FILE}" /export:GetExportedFuncAddrs,@1 /export:SetImportedFuncAddrs,@2)

