
set(INNER_LOOP_HEADERS ${INNER_LOOP_HEADERS} ${CMAKE_CURRENT_SOURCE_DIR}/EMTG_innerloop_solution.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/EMTG_WORHP_interface.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/FilamentWalker.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/monotonic_basin_hopping.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLPoptions.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_interface.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_solution_acceptance.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_sparse_derivative_layout.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_solver_factory.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_solver_selection.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/NLP_solver_status.h
                                             ${CMAKE_CURRENT_SOURCE_DIR}/IPOPT_status.h)
												  
set(INNER_LOOP_SOURCE ${INNER_LOOP_SOURCE} ${CMAKE_CURRENT_SOURCE_DIR}/EMTG_innerloop_solution.cpp
								           ${CMAKE_CURRENT_SOURCE_DIR}/EMTG_WORHP_interface.cpp
                                           ${CMAKE_CURRENT_SOURCE_DIR}/FilamentWalker.cpp
                                           ${CMAKE_CURRENT_SOURCE_DIR}/monotonic_basin_hopping.cpp
                                           ${CMAKE_CURRENT_SOURCE_DIR}/NLPoptions.cpp
                                           ${CMAKE_CURRENT_SOURCE_DIR}/NLP_interface.cpp
                                           ${CMAKE_CURRENT_SOURCE_DIR}/NLP_solver_factory.cpp)

if(EMTG_NLP_SOLVER STREQUAL "SNOPT")
    set(INNER_LOOP_HEADERS ${INNER_LOOP_HEADERS} ${CMAKE_CURRENT_SOURCE_DIR}/SNOPT_interface.h
                                                 ${CMAKE_CURRENT_SOURCE_DIR}/SNOPT_status.h
                                                 ${CMAKE_CURRENT_SOURCE_DIR}/snoptProblemExtension.h)
    set(INNER_LOOP_SOURCE ${INNER_LOOP_SOURCE} ${CMAKE_CURRENT_SOURCE_DIR}/SNOPT_interface.cpp)
elseif(EMTG_NLP_SOLVER STREQUAL "IPOPT")
    set(INNER_LOOP_HEADERS ${INNER_LOOP_HEADERS} ${CMAKE_CURRENT_SOURCE_DIR}/IPOPT_interface.h)
    set(INNER_LOOP_SOURCE ${INNER_LOOP_SOURCE} ${CMAKE_CURRENT_SOURCE_DIR}/IPOPT_interface.cpp)
endif()
                                           
set(INNER_LOOP_FILES ${INNER_LOOP_FILES} ${INNER_LOOP_HEADERS} ${INNER_LOOP_SOURCE} PARENT_SCOPE)
    

    
