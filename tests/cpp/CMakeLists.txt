get_property(EMTG_SOURCE_INCLUDE_DIRECTORIES
    DIRECTORY ${PROJECT_SOURCE_DIR}/src
    PROPERTY INCLUDE_DIRECTORIES)

function(add_nlp_contract target source)
    add_executable(${target} ${source})
    target_compile_features(${target} PRIVATE cxx_std_17)
    target_include_directories(${target} SYSTEM PRIVATE
        ${EMTG_SOURCE_INCLUDE_DIRECTORIES})
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Werror)
    endif()
    add_test(NAME ${target} COMMAND ${target})
endfunction()

add_nlp_contract(nlp_pure_contract test_nlp_pure_contract.cpp)
add_nlp_contract(nlp_interface_contract test_nlp_interface_contract.cpp)
target_link_libraries(nlp_interface_contract PRIVATE emtg)

if(EMTG_NLP_SOLVER STREQUAL "IPOPT")
    add_library(ipopt_adapter_compile_contract OBJECT
        ${PROJECT_SOURCE_DIR}/src/InnerLoop/IPOPT_interface.cpp)
    target_compile_features(ipopt_adapter_compile_contract PRIVATE cxx_std_17)
    target_include_directories(ipopt_adapter_compile_contract SYSTEM PRIVATE
        ${EMTG_SOURCE_INCLUDE_DIRECTORIES})
    target_link_libraries(ipopt_adapter_compile_contract PRIVATE PkgConfig::IPOPT)
    if(MSVC)
        target_compile_options(ipopt_adapter_compile_contract PRIVATE /W4 /WX)
    else()
        target_compile_options(ipopt_adapter_compile_contract PRIVATE
            -Wall -Wextra -Werror)
    endif()

    add_nlp_contract(ipopt_adapter_contract test_ipopt_adapter.cpp)
    target_link_libraries(ipopt_adapter_contract PRIVATE emtg PkgConfig::IPOPT)
    set_tests_properties(ipopt_adapter_contract PROPERTIES
        FAIL_REGULAR_EXPRESSION
            "Derivative checker detected [1-9][0-9]* error\\(s\\)")
endif()