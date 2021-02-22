
## Generating md files

We need to generate md files for the static site generator (SSG) to read.

We use Jekyll, with the [just-the-docs theme](https://pmarsceill.github.io/just-the-docs/).

### Plan

The pages will include:
* [x] main program source code
* [x] outputs of the main program (figures and text output)
  * run using Matlab's [engine for Python](https://www.mathworks.com/help/matlab/matlab-engine-for-python.html)
* [x] aux program source code (hidden by default)
* [x] links to the source files on GH (master branch)
* [ ] links to relevant md source files (editable ones, not auto-generated ones)

Other:
* [ ] Make use of SSG filters instead of including HTML in the md files.
