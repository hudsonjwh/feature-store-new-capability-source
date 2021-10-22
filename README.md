# Sample Courseware Repo

## Release Notes
This course has been tested on AWS, MSA and GCP.<br/>

## Requirements
| Cloud |        DBR | Cluster Mode | Worker Type     | Min Cores |
|:-----:|:----------:|:------------:|:----------------|:---------:|
|   AWS | 9.1 LTS ML |  Single Node | i3.xlarge       | 4 cores   |
|   MSA | 9.1 LTS ML |  Single Node | Standard_DS3_v2 | 4 cores   |
|   GCP | 9.1 LTS ML |  Single Node | n1-standard-4   | 4 cores   |

## Student Resources
* Student-Facing Repo: https://github.com/databricks-academy/sample-courseware-repo
* Student DBC: See the [Latest releases](https://github.com/databricks-academy/natural-language-processing/releases/latest) section of the student-facing repo
* Student Slides (PDF): See the [Latest releases](https://github.com/databricks-academy/natural-language-processing/releases/latest) section of the student-facing repo

## Instructor Resources
* [Google Slides - Instructor](https://docs.google.com/presentation/d/1IE_nUvYm9cqlBznrNo_OJTX2eds8Xw4pTBU5IP2PUMg/edit?usp=sharing)

## Preparatory Resources
* T3 Videos - none

## Additional Resources
* [Student Repository](https://github.com/databricks-academy/natural-language-processing)
* [Source Repository](https://github.com/databricks-academy/natural-language-processing-source) (private)
* [Report an issues with this course](https://docs.google.com/forms/d/e/1FAIpQLScQAskPEY4Rq-Y0csOfZCGdDo_JjEphWSxfgLTZIof0cj5CaQ/viewform?usp=pp_url&entry.407881500=Natural+Language+Processing&entry.471704161=Instructor-Led)
* Review issue status - Coming Soon!
* Test Results - Coming Soon!
* [Create a publishing request for this course](https://docs.google.com/forms/d/e/1FAIpQLScD3Tn3t4u9i-10SYPCt1Qd1P4o2RiX6O_S3xn4HgQ2HvSNdQ/viewform?usp=pp_url&entry.407881500=Natural+Language+Processing&entry.471704161=Instructor-Led)

## Building this Course

This course no longer uses the `BDC` tool for assembling the notebooks into a course. `BDC` has been supplanted by the `Course Assembly Tool` (`CAT`) found within the python project https://github.com/databricks-academy/dbacademy

This course makes use of the following recourses for building and publishing:
* Student facing resources are published to the sibling repo at https://github.com/databricks-academy/natural-language-processing
* DBCs, when desired can be found at https://github.com/databricks-academy/natural-language-processing/releases/latest
* Both repos can found in the three Curriculum workspaces (AWS, MSA & GCP).
    * See `/Repos/Published/natural-language-processing-source` for the source repo
    * See `/Repos/Published/natural-language-processing-STUDENT-COPY` for the student-facing, public repo.
    * It is strongly recomended that all development occur in the AWS Curriculum workspace folder to minimize merge conflects and other development delays associated with PRs as opposed to private instances or forks.
    * Note: Curriculum Contributors (e.g. instructors, RSAs, etc) will be able to make edits, but will be unable to push changes to the git repo allowing the curriculum team to first review any changes.
* All testing and publishing scripts can be found in the `Build-Scripts` subfolder:
    * `/Build-Scripts/Test-Config` contains course-specific configuration information such as course-name, libraries required for testing, specification of testing pools, etc, and contains common information used by other publishing & testing steps. 
    * `/Build-Scripts/Publish-All` will publish the source notebooks into the sibling public repo. Note this script does not invote any tests.
    * `/Build-Scripts/Test-All-Source` will test all the source notebooks, occasionally invoked manually with a simple `Run All` to quickly test changes.
    * `/Build-Scripts/Test-All-Published` will test all the publisehd notebooks, occasionally invoked manually with a simple `Run All` to quickly test the publishing processes as well as the student-facing version of the course.
    * `/Build-Scripts/Preheat-VMs` is used exclusively by the test-job in each cloud to start N number of VMs from the pool at the onset of testing, ensuring that those VMs are hot and ready once the test sycle gets to testing all notebooks asyncrounsly.
    * `/Build-Scripts/Update-Git-Branch` is used exclusively by the test-job in each cloud to update the workspace repos to the lastest version of the `Published` branch before execution of any tests.
* In all three curriculum workspaces (AWS, MSA & GCP) both the source and student-facing notebooks are automatically tested every Saturday.

## Publishing Steps
The recomended practice to publish this course includes:

### Step #1 - Update and validate courseware state
1. Update `/Build-Scripts/Publish-All` to reflect the correct version number and DBR. Both attributes are found in the first lines of Cmd #3.
2. Check for any pending, uncommited changes to the source notebooks. If changes are found, these must be committed before publishing else the tests results on the other two clouds will be inconsistent with the primary workspace that will pickup and test against uncommitted changes.

### Step #2 - Execute the test jobs in all three clouds.
* These can be found as a scheduled job in the AWS, MSA and GCP Curriculum Workspace
* Hint: Filter the jobs by `[SUITE]` to quickly see the preconfiuged test suite jobs.
* Once the test-suite-job is opened, simply click `Run Now` to start the test cycle
* Once started, select `View Details` to track the status of the job
* The duration of the test will varry from 15 minutes to several hours depending on the complexity of the course.
* Naturally, if **ANY** test fails in **ANY** cloud, stop the publishing process and address all issues.

### Step #3 - Publish to the student-facing, public repo
1. Publish the course to the student-facing public repo by running `/Build-Scripts/Publish-All`.
    * Note, while the test cycle will publish most artfiacats, it is not a complete publish as it is published in a "test" mode.
    * The duration of this step is usually a few seconds to a minute.
2. Commit all changes to the student-facing public repo.
    * Note: there will always be at least one changed file, `Version Info`, which will be updated the the current version, date and time.
    * At this point the couse is considered "publsihed" in that the students will have avilable this latest version should that import the project via Databricks Repos or issue a pull request on an existing copy of the repo.

### Step #4 - Publish the DBC to the Releases page
1. Create the DBC file by exporting the from the student-facing repo the folder `/Repos/Published/natural-language-processing-STUDENT-COPY/Scalable-NLP-with-Apache-Spark` and downloading it to your machine.
2. In GitHub, open the student-facing public repo.
3. Go the `Releases` (the link can be found on the right-side of the screen just below `About`).
4. Note the existing conventions as you create your release:
    * The tag will be of the form `vX.Y.Z` where X is the major release number (major course change), Y is is the minor release number (minor course updates) and Z is the build number (reserved for superficial typos and bug fixes)
    * The title will consist of the course's full name as it appears in the course catalog followed by the version number.
    * The description will contain three key attributes: The DBR (typically the latest LTS), the minimum number of course (typically 4), and the recomended Cluster Mode (typically Single Node). We do not include cloud-specific VM preferences here.
5. Click on `Draft a new release`
6. Provide the required tag, title and description.
7. Upload the DBC file created in step #6 above.
8. Upload the last version of the slides, if any
    * Note: If the slides are known to be unmodified, you can download them from the previus version.
9. Optionally select `This is a pre-release` if this a beta release.
10. Click `Publish release`

### Step #5 - Update the Release Notes (README.md)
1. Go back to the source repo and open the `README.md` file.
2. Update the `Release Notes` section which will include know testing failures, problems specific to a notebook and/or cloud, and any other general information.
3. Update the `Requirements` section to reflect the DBR under which this course was tested, the worker type used in testing, and the minium number of cores.
4. Update the `Classroom Resources` section if anything has changed.
  * Note: Student DBC and Student Slides should remain unchanged as they simply point the the latest relase.
  * Google Slides may have change, confirm that the link points to the correct set.
5. Review all other sections - in most cases they will not change.
   
  
### Step #6 Congratulate yourself, the course is published!
