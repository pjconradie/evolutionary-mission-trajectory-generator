
===============================================================================================================

Modified Evolutionary Mission Trajectory Generator (EMTG) Open Source Release
Originating author: PJ Conradie
Mainainer: Surreal Technologies
Version: 9.02
License: NASA Open Source Agreement (https://www.nasa.gov/open/open-source-development.html)
Notices and Disclaimers: See the bottom of the README

===============================================================================================================

# Purpose

The contents of this modified NASA GSFC public software release distribution contains all of the source code and documentation for the 
Evolutionary Mission Trajectory Generator (EMTG) as distributed by NASA GSFC.

Its core enhancement is the integration of the Open Source IPOPT NPL solver. This allows you to use IPOPT when solving trajectories instead of having to rely on proprietary SNOPT.

Additionally enhancements includes a framework to deploy EMTG + IPOPT to a Docker container running Linux.

The deployment is verified by a set of unit, regression, integration and baselining tests described in detail under [[testatron/ipopt/tests/readme]].

# Todo

The documentation and repeatability of the clean bootstrapped Linux Docker Image case eluded to in [[testatron/ipopt/tests/readme]] has not been completed (documentation) or illustrated to be repeatable yet. This is the next set of work to be done. (20206-10-16)

Based on the [ADSGNC](https://github.com/pjconradie/adsgnc) repository, the modified EMTG will also require the ability to archive and zip the source code in order for it to be deployed to a third party system. This is the second priority to complete. (20206-10-16)


## Bootstrapped Linux Docker Image

1. Create, destroy and use docker images and containers.
2. Pass deployment tests. Includes all the tests under [[testatron/ipopt/tests/readme]].
3. Pass 3rd party deployment tests (ADSGNC will be the first user).

## EMTG Package

1. See 

## Update Baselined Checklist table

Update [[baselined_checklist]] tables, especially the readme that describes the concept of operations
- Refinement
- Classification
- Decision Log
- Candidate Artifact
- Manual Decision
- README

# Original NASA EMTG readme

The original EMTG readme is located under [README.opensource](https://github.com/pjconradie/evolutionary-mission-trajectory-generator/blob/dev/README.opensource "README.opensource")

