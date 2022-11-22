# GWF Publications

These are basic instructions on generating the GWF Publications website as seen on <https://gwf-uwaterloo.github.io/gwf-publications/>.

## Generating the website

### Prerequisites

To build the Anthology website, you will need:

+ **Python 3.8** or higher
+ Python packages listed in `bin/requirements.txt`; to install, run `pip -r bin/requirements.txt`
+ [**Hugo 0.58.3**](https://gohugo.io) or higher (can be [downloaded directly from
  their repo](https://github.com/gohugoio/hugo/releases); the ***extended version*** is required!)
+ [**bibutils**](https://sourceforge.net/p/bibutils/home/Bibutils/) for creating
  non-BibTeX citation formats (not strictly required to build the website, but
  without them you need to invoke the build steps manually as laid out in the
  [detailed README](README_detailed.md))
+ *optional*: If you install `libyaml-dev` and `Cython` before running `make`
   the first time, the libyaml C library will be used instead of a python
   implementation, speeding up the build.

### Building and deployment with GitHub
### Cloning

Clone the Anthology repo to your local machine:

```bash
$ git clone https://github.com/gwf-uwaterloo/gwf-publications
```

### Generating

Provided you have correctly installed all requirements, building the website
should be as simple running `make` from the directory to which
you cloned the repo.

We used the command below because of the domain:
```bash
sudo ANTHOLOGY_PREFIX="https://gwf-uwaterloo.github.io/gwf-publications" make
```
The fully generated website will be in `build/website` afterwards. You can see the resulting website by launching
a local webserver with `make serve`, which will serve it at http://localhost:8000.

Note that building the website is quite a resource-intensive process;
particularly the last step, invoking Hugo, uses about 18~GB of system memory.
Building the anthology takes about 10 minutes on a laptop with an SSD.

(**Note:** This does *not* mean you need this amount of RAM in your system; in
fact, the website builds fine on a laptop with 8 GB of RAM.  The system might
temporarily slow down due to swapping, however.  The figure of approx. 18 GB is
the maximum RAM usage reported when running `hugo --minify --stepAnalysis`.)

The anthology can be viewed locally by running `hugo server` in the
`hugo/` directory.  Note that it rebuilds the site and therefore takes
about a minute to start.
