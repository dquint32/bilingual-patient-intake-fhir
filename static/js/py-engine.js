/* py-engine.js — run this project's tested Python package in the browser.
 *
 * Loads Pyodide (CPython compiled to WebAssembly), installs the package's
 * dependencies, copies the project's own .py files into Pyodide's virtual file
 * system, and exposes one Python function to JavaScript. The live demo therefore
 * runs exactly the code covered by the pytest suite — no server, no duplicate
 * JavaScript implementation of the rules.
 */
(function () {
  'use strict';

  var PYODIDE_VERSION = '314.0.7';
  var INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v' + PYODIDE_VERSION + '/full/';

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.async = true;
      s.onload = resolve;
      s.onerror = function () { reject(new Error('Could not load ' + src)); };
      document.head.appendChild(s);
    });
  }

  /**
   * @param {object} opts
   * @param {Object<string,string>} opts.files   python path -> URL, e.g. {'cds/service.py': 'backend/cds/service.py'}
   * @param {string[]} [opts.packages]           Pyodide-built packages, e.g. ['pydantic']
   * @param {string[]} [opts.pipPackages]        pure-Python wheels from PyPI via micropip
   * @param {string} opts.entry                  Python expression returning the callable, e.g. 'cds.service.calculate_json'
   */
  window.createPyEngine = function (opts) {
    var ready = null;

    function boot() {
      return (window.loadPyodide ? Promise.resolve() : loadScript(INDEX_URL + 'pyodide.js'))
        .then(function () { return window.loadPyodide({ indexURL: INDEX_URL }); })
        .then(function (py) {
          var pkgs = (opts.packages || []).slice();
          if ((opts.pipPackages || []).length) pkgs.push('micropip');
          return py.loadPackage(pkgs).then(function () { return py; });
        })
        .then(function (py) {
          if (!(opts.pipPackages || []).length) return py;
          return py.pyimport('micropip').install(opts.pipPackages).then(function () { return py; });
        })
        .then(function (py) {
          var root = '/home/pyodide/';
          return Promise.all(Object.keys(opts.files).map(function (path) {
            return fetch(opts.files[path], { cache: 'no-cache' }).then(function (r) {
              if (!r.ok) throw new Error('Could not load ' + opts.files[path] + ' (' + r.status + ')');
              return r.text();
            }).then(function (src) {
              var dir = (root + path).replace(/\/[^/]+$/, '');
              py.FS.mkdirTree(dir);
              py.FS.writeFile(root + path, src);
            });
          })).then(function () {
            var mod = opts.entry.replace(/\.[^.]+$/, '');
            py.runPython('import importlib, ' + mod.split('.')[0] + '\nimportlib.invalidate_caches()');
            return py.runPython('import ' + mod + '\n' + opts.entry);
          });
        });
    }

    return {
      /** Start loading (idempotent). Resolves to the Python callable. */
      load: function () {
        if (!ready) {
          ready = boot().catch(function (err) { ready = null; throw err; });
        }
        return ready;
      },
      /** Call the entry function with a string argument; resolves to its string result. */
      call: function (arg) {
        return this.load().then(function (fn) { return fn(arg); });
      }
    };
  };
})();
