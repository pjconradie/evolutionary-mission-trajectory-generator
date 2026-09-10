add_executable(nlp_solver_contract test_nlp_solver_contract.cpp)
target_compile_features(nlp_solver_contract PRIVATE cxx_std_17)
target_include_directories(nlp_solver_contract PRIVATE
    ${PROJECT_SOURCE_DIR}/src/Core
    ${PROJECT_SOURCE_DIR}/src/InnerLoop)
target_link_libraries(nlp_solver_contract PRIVATE emtg)

if(MSVC)
    target_compile_options(nlp_solver_contract PRIVATE /W4 /WX)
else()
    target_compile_options(nlp_solver_contract PRIVATE -Wall -Wextra -Werror)
endif()

add_test(NAME nlp_solver_contract COMMAND nlp_solver_contract)