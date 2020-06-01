
## Generating md files

We need to generate md files for the static site generator (SSG) to read.

Currently planning to use Jekyll, with the just-the-docs theme.

### Plan

The pages will include:
* [x] main program source code
* [ ] outputs of the main program (figures and text output)
  * run using Matlab's matlab.engine for Python
* [ ] aux program source code (hidden by default)
* [ ] links to the source files on GH (master branch)
  * links to the md files on gh-pages branch?

May nest by chapter, since I plan to have the navigation nested in that way.

Make use of SSG filters instead of including HTML in the md files.
