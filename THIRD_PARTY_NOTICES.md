# Third-Party Notices and Licenses

Video Screenshot Extractor (影片配圖擷取器) bundles or utilizes several open-source components. This document provides precise information on these third-party packages, their official sources, and their corresponding licenses.

---

## 1. FFmpeg & FFprobe (Gyan.dev Essentials Windows Build)

* **Project**: FFmpeg
* **Official Website**: https://ffmpeg.org
* **Binary Build Source**: Gyan.dev Windows Builds (https://www.gyan.dev/ffmpeg/builds/ & https://github.com/GyanD/codexffmpeg)
* **Version**: 9.0.1 (Essentials Build)
* **License**: GNU General Public License version 3 (GPL-3.0)
* **Notice & Compliance**:
  The precompiled static binaries (`ffmpeg.exe`, `ffprobe.exe`) provided by Gyan.dev are built with `--enable-gpl` (including libraries such as `libx264`, `libx265`) and are therefore licensed under the GNU General Public License v3.0.
  Complete source code for FFmpeg can be downloaded from:
  - FFmpeg upstream: `git clone git://source.ffmpeg.org/ffmpeg.git` or https://ffmpeg.org/download.html
  - Build scripts and exact source tree used by Gyan.dev: https://github.com/GyanD/codexffmpeg
  Video Screenshot Extractor interacts with FFmpeg and FFprobe solely through standard, non-linked process execution (`subprocess`).

---

## 2. yt-dlp

* **Project**: yt-dlp
* **Official Website**: https://github.com/yt-dlp/yt-dlp
* **Release Source**: https://github.com/yt-dlp/yt-dlp/releases
* **Version**: 2026.08.19
* **License**: The Unlicense (Public Domain Dedication)
* **License Text**:
  This is free and unencumbered software released into the public domain.

  Anyone is free to copy, modify, publish, use, compile, sell, or
  distribute this software, either in source code form or as a compiled
  binary, for any purpose, commercial or non-commercial, and by any
  means.

  In jurisdictions that recognize copyright laws, the author or authors
  of this software dedicate any and all copyright interest in the
  software to the public domain. We make this dedication for the benefit
  of the public at large and to the detriment of our heirs and
  successors. We intend this dedication to be an overt act of
  relinquishment in perpetuity of all present and future rights to this
  software under copyright law.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
  OTHER DEALINGS IN THE SOFTWARE.

---

## 3. Deno

* **Project**: Deno
* **Official Website**: https://deno.land
* **Official Repository**: https://github.com/denoland/deno
* **Version**: 2.9.6
* **License**: MIT License
* **Copyright**: Copyright 2018-2026 the Deno authors.
* **License Text**:
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

---

## 4. Python Runtime & Standard Library (including Tkinter / Tcl / Tk)

* **Project**: Python
* **Official Website**: https://www.python.org
* **License**: Python Software Foundation (PSF) License Agreement version 2
* **Tcl/Tk License**: Regulated by the Regents of the University of California, Sun Microsystems, Inc., Scriptics Corporation, and other parties (BSD-style permissive license).
* **Notice**: Python and Tcl/Tk are distributed under their respective permissive open-source licenses. Full license texts can be inspected at https://docs.python.org/3/license.html.


---

## 5. yt-dlp-threads

* **Project**: yt-dlp-threads
* **Source**: https://github.com/tribixbite/yt-dlp-threads
* **Purpose**: yt-dlp extractor plugin for publicly viewable Threads video posts.
* **License**: The Unlicense (Public Domain Dedication)
* **Bundling**: The extractor source is vendored under `plugins/yt_dlp_plugins/extractor/threads.py` and loaded by the bundled yt-dlp executable.
