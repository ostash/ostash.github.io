date: 2026-04-04
description: Establishing a verified baseline: building LLVM with no backends and running the test suite.
license: CC-BY-4.0
slug: llvm-ia16-build-setup
tags: 8086, backend, compilers, ia16, llvm
title: Setting up an LLVM development build

The [first post]({filename}01-llvm-ia16-intro.md) ended with a promise: the next step is getting LLVM to recognise
`ia16` as a valid architecture.
Before touching any source code, I want a build configured cleanly for development work.
A few CMake flags chosen once save a lot of confusion later.

LLVM's build system is driven by [CMake](https://cmake.org/), which generates project files for an underlying build tool
— Ninja in this case.
CMake does not build anything directly; it reads the `CMakeLists.txt` files in the source tree and outputs a build graph
that Ninja executes.
The LLVM source tree is a monorepo that consists of many components at once: LLVM core, Clang, Flang, LLDB, LLD, and
more.
CMake flags control which components are compiled, which CPU-architecture backends are included, and whether tests,
examples, and documentation targets are generated.

## CMake configuration

The build lives in a `build/` subdirectory at the repository root.
The generator is [Ninja](https://ninja-build.org/) — it is lean by design: fast startup, a compact build graph, and more
aggressive parallelism than Make.

```shell
cmake -B build -S llvm \
  -G Ninja \
  -DBUILD_SHARED_LIBS=ON \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DLLVM_ENABLE_PROJECTS="" \
  -DLLVM_ENABLE_RUNTIMES="" \
  -DLLVM_INCLUDE_BENCHMARKS=OFF \
  -DLLVM_INCLUDE_DOCS=OFF \
  -DLLVM_INCLUDE_EXAMPLES=OFF \
  -DLLVM_INCLUDE_TESTS=ON \
  -DLLVM_INCLUDE_UTILS=ON \
  -DLLVM_OPTIMIZED_TABLEGEN=ON \
  -DLLVM_TARGETS_TO_BUILD=""
```

### Flag breakdown

| Flag | Value | Reason |
|------|-------|--------|
| `-G Ninja` | Ninja | Faster incremental builds than Make. Ninja parallelises more aggressively. |
| `-DBUILD_SHARED_LIBS=ON` | `ON` | Each LLVM library becomes a separate `.so` instead of one big static archive. This matters for Debug builds: they're huge, and splitting them means only the changed library (and the final binary) needs relinking after I edit something. It's also a win for disk space — without this, a static Debug build easily hits tens of gigabytes because every tool embeds its own copy of the entire library set. |
| `-DCMAKE_BUILD_TYPE=Debug` | `Debug` | Unoptimised binary, full debug symbols. Essential for development. |
| `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` | `ON` | Needed by clangd language server for code navigation. |
| `-DLLVM_ENABLE_ASSERTIONS=ON` | `ON` | Turns on all the `assert()`-based sanity checks baked into LLVM. If I pass an illegal IR value, reference a target that doesn't exist, or violate some pass's contract, an assertion fires with a clear message. Without this, those mistakes silently corrupt the output or crash later in a confusing place. |
| `-DLLVM_ENABLE_PROJECTS=""` | `""` | Disables all non-LLVM-core projects (Clang, Flang, LLDB, etc.). |
| `-DLLVM_ENABLE_RUNTIMES=""` | `""` | Disables all runtime libraries (libc++, compiler-rt, llvm-libc, etc.). |
| `-DLLVM_INCLUDE_BENCHMARKS=OFF` | `OFF` | Not useful during early bring-up. |
| `-DLLVM_INCLUDE_DOCS=OFF` | `OFF` | Suppresses documentation build targets entirely. |
| `-DLLVM_INCLUDE_EXAMPLES=OFF` | `OFF` | Skips `examples/` — tutorials unrelated to backend work. |
| `-DLLVM_INCLUDE_TESTS=ON` | `ON` | Generates the `check-*` build targets, so `ninja check-llvm` exists as a command. |
| `-DLLVM_INCLUDE_UTILS=ON` | `ON` | Generates targets for the utility programs under `llvm/utils/` — like `FileCheck` and `not`, which `lit` invokes from `RUN:` lines. |
| `-DLLVM_OPTIMIZED_TABLEGEN=ON` | `ON` | Creates a Release-mode `llvm-tblgen` under `build/NATIVE/bin/` for CMake to use during the build. It's a build-time helper only (never installed). Without it, `.td` file processing uses the slow Debug binary (full of assertions), which noticeably slows the initial build. |
| `-DLLVM_TARGETS_TO_BUILD=""` | `""` | No backends. Baseline before `ia16` is added; reduces build time. |

Few notes on some of those flags:

- `LLVM_ENABLE_ASSERTIONS=ON` is the default when `CMAKE_BUILD_TYPE=Debug` so writing it out is technically redundant.
But it documents intent, and I'd rather be explicit about a flag that changes the observable behaviour of the binary.
- `LLVM_TARGETS_TO_BUILD=""` is the most important flag for this exercise.
Every other LLVM build I've seen online builds at least the host target (i.e. `X86`).
Setting this to empty gives a clean baseline: if the core infrastructure is broken, I see it before any target-specific
code exists to confuse the picture.

The flags above also illustrate a pattern that appears across LLVM's CMake variables: the `LLVM_INCLUDE_*` /
`LLVM_BUILD_*` split:

- `LLVM_INCLUDE_TESTS=ON` (the default) generates the `check-*` CMake targets, making `ninja check-llvm` a usable
command.
It does not, however, build the unit test binaries unconditionally.
- `LLVM_BUILD_TESTS=ON` (default: `OFF`) would build those binaries as part of a plain `ninja` invocation — useful on a
CI server that always runs tests, but wasteful during normal development where tests are built on demand.

The same `INCLUDE`/`BUILD` split applies to utils, tools, examples, and benchmarks.

## Building what is needed

I only need to build `llc` (the LLVM Static Compiler) itself:

```shell
ninja -C build llc
```

## Verifying the empty target list

```console
$ ./bin/llc --version
LLVM (http://llvm.org/):
  LLVM version 22.1.2
  DEBUG build with assertions.
  Default target:
  Host CPU: skylake

  Registered Targets:
    (none)
```

This is the expected baseline.
`DEBUG build with assertions` confirms the CMake flags took effect.
`Default target:` is blank — no default without a backend.
`Registered Targets: (none)` is the empty list.
When the `ia16` backend is registered, `ia16` will appear here.

## Running the baseline test suite

[`lit`](https://llvm.org/docs/CommandGuide/lit.html) (the LLVM Integrated Tester) is LLVM's test runner.
It's flexible — it can drive different kinds of tests in different ways.

Regression tests (under `llvm/test/` as `.ll`, `.mir`, or similar files) use the `ShTest` format.
`lit` reads embedded `RUN:` directives that spell out shell commands, and `CHECK:` directives to match the output.

Unit tests are C++ binaries under `llvm/unittests/`, built with [GoogleTest](https://github.com/google/googletest).
`lit` handles these differently — `llvm/test/Unit/lit.cfg.py` uses a separate format (`lit.formats.GoogleTest`).
Instead of directive parsing, it discovers the test binaries themselves, discovers their test cases, and runs them with
sharding to use all available CPU cores.

Both formats feed into a single test run, so `ninja check-llvm` invokes `lit` once and gets a combined report.

### What test targets exist

The main CMake test targets are:

| Target | What it runs |
|--------|--------------|
| `check-all` | Every `lit` testsuite across all enabled projects, including `check-lit` (`lit`'s own self-tests). With only LLVM enabled, this means `check-llvm` plus `check-lit`. |
| `check-llvm` | The LLVM regression tests and the GoogleTest unit tests — the main development target. `lit` runs the entire `build/test/` directory tree, which includes `build/test/Unit/` where unit test binaries live. |
| `check-llvm-unit` | Only the GoogleTest unit tests in `llvm/unittests/`. |
| `check-lit` | `lit` own self-tests — exercises the test runner itself, not LLVM code. |

### Running the tests

`ninja check-llvm` runs `lit` with the default flags `-sv`.
`-s` hides most output and just shows a progress bar; `-v` makes failures print their full command trace.
On a clean run, all I see is the progress bar crawling along with an ETA.

<style type="text/css">
.ansi1 { font-weight: bold; }
.ansi31 { color: #aa0000; }
.ansi36 { color: #00aaaa; }
</style>

<pre>
<span class="ansi1 ansi36">                     -- Testing: 60862 tests, 8 workers --</span>
 12% <span class="ansi31">[<span class="ansi1">=======----------------------------------------------------</span>]</span> ETA: 00:06:29
LLVM :: TableGen/SDNodeInfoEmitter/namespace.td
</pre>

To see the result of every test — passes, skips, expected failures — run `lit` directly with `-a`:

```shell
build/bin/llvm-lit -a build/test/
```

To run only a subtree, point `lit` at the relevant directory:

```shell
build/bin/llvm-lit build/test/tools/llc/
```

Or scope a `ninja check-llvm` run to a subset using the `LIT_FILTER` environment variable, which `lit` treats as a regex
matched against test paths:

```shell
LIT_FILTER="save-stats" ninja -C build check-llvm
```

Four status labels matter:

- `PASS` — worked.
- `UNSUPPORTED` — skipped (usually because a `REQUIRES:` guard names a backend we don't have).
- `XFAIL` — expected to fail, and it did. Not a problem.
- `FAIL` — something broke. These are what I investigate.

Unit test output looks strange — `MC/./MCTests/6/9` means shard 6 of 9 for the `MCTests` binary.
The actual readable test name shows up in the error details.

### The three "unexpected" failures

All three fail for the same reason: they expect a backend to exist, and we have none.

**`LLVM-Unit :: MC/MCTests/TargetRegistry/TargetHasArchType`**

```text
FAIL: LLVM-Unit :: MC/./MCTests/6/9 (1 of 60862)
******************** TEST 'LLVM-Unit :: MC/./MCTests/6/9' FAILED ********************
Script(shard):
--
GTEST_OUTPUT=json:build/unittests/MC/./MCTests-LLVM-Unit-1627473-6-9.json GTEST_SHUFFLE=0 GTEST_TOTAL_SHARDS=9 GTEST_SHARD_INDEX=6 build/unittests/MC/./MCTests
--

Script:
--
build/unittests/MC/./MCTests --gtest_filter=TargetRegistry.TargetHasArchType
--
llvm/unittests/MC/TargetRegistry.cpp:42: Failure
Expected: (Count) != (0), actual: 0 vs 0


/mnt/data/rootopt/home/ostash/repos/llvm-project/llvm/unittests/MC/TargetRegistry.cpp:42
Expected: (Count) != (0), actual: 0 vs 0
```

This test counts all registered backends and asserts the count is at least 1.
With zero backends, it fails — which is exactly what the test is *designed* to do.
The comment in the source even says so: it's a sanity check to catch the mistake of forgetting to call
`InitializeAllTargetInfos`.

**`LLVM :: tools/llc/save-stats.ll`**

```text
FAIL: LLVM :: tools/llc/save-stats.ll (2 of 60862)
******************** TEST 'LLVM :: tools/llc/save-stats.ll' FAILED ********************
Exit Code: 1

Command Output (stdout):
--
# RUN: at line 4
rm -rf build/test/tools/llc/Output/save-stats.ll.tmp.dir && mkdir -p build/test/tools/llc/Output/save-stats.ll.tmp.dir && cd build/test/tools/llc/Output/save-stats.ll.tmp.dir
# executed command: rm -rf build/test/tools/llc/Output/save-stats.ll.tmp.dir
# executed command: mkdir -p build/test/tools/llc/Output/save-stats.ll.tmp.dir
# executed command: cd build/test/tools/llc/Output/save-stats.ll.tmp.dir
# RUN: at line 6
build/bin/llc --save-stats=obj -o build/test/tools/llc/Output/save-stats.ll.tmp.s llvm/test/tools/llc/save-stats.ll && cat build/test/tools/llc/Output/save-stats.ll.tmp.stats | build/bin/FileCheck llvm/test/tools/llc/save-stats.ll
# executed command: build/bin/llc --save-stats=obj -o build/test/tools/llc/Output/save-stats.ll.tmp.s llvm/test/tools/llc/save-stats.ll
# .---command stderr------------
# | build/bin/llc: error: unable to get target for '', see --version and --triple.
# `-----------------------------
# error: command failed with exit status: 1
```

`llc` is called on an IR file with no triple specified.
With no backends available, `llc` can't pick a target and errors out.
The test itself is missing a `REQUIRES:` guard — that's a bug in the test, not in the build.

**`LLVM :: LTO/empty-triple.ll`**

```text
FAIL: LLVM :: LTO/empty-triple.ll (3 of 60862)
******************** TEST 'LLVM :: LTO/empty-triple.ll' FAILED ********************
Exit Code: 1

Command Output (stdout):
--
# RUN: at line 1
build/bin/llvm-as < llvm/test/LTO/empty-triple.ll >build/test/LTO/Output/empty-triple.ll.tmp1
# executed command: build/bin/llvm-as
# RUN: at line 2
build/bin/llvm-lto -exported-symbol=main -filetype=asm -o - build/test/LTO/Output/empty-triple.ll.tmp1  2>&1 | build/bin/FileCheck llvm/test/LTO/empty-triple.ll
# executed command: build/bin/llvm-lto -exported-symbol=main -filetype=asm -o - build/test/LTO/Output/empty-triple.ll.tmp1
# note: command had no output on stdout or stderr
# error: command failed with exit status: 1
# executed command: build/bin/FileCheck llvm/test/LTO/empty-triple.ll
# .---command stderr------------
# | llvm/test/LTO/empty-triple.ll:7:16: error: CHECK-LABEL: expected string not found in input
# | ; CHECK-LABEL: main
# |                ^
# | <stdin>:1:1: note: scanning from here
# | llvm-lto: error loading file 'build/test/LTO/Output/empty-triple.ll.tmp1': Unable to find target for this triple (no targets are registered)
# | ^
# | <stdin>:1:19: note: possible intended match here
# | llvm-lto: error loading file 'build/test/LTO/Output/empty-triple.ll.tmp1': Unable to find target for this triple (no targets are registered)
# |                   ^
# | 
# | Input file: <stdin>
# | Check file: llvm/test/LTO/empty-triple.ll
# | 
# | -dump-input=help explains the following input dump.
# | 
# | Input was:
# | <<<<<<
# |            1: llvm-lto: error loading file 'build/test/LTO/Output/empty-triple.ll.tmp1': Unable to find target for this triple (no targets are registered) 
# | label:7'0     X~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ error: no match found
# | label:7'1                       ?                                                                                                                                                                            possible intended match
# | >>>>>>
# `-----------------------------
# error: command failed with exit status: 1
```

`llvm-lto` reads a bitcode file with an empty triple and immediately errors: "Unable to find target for this triple (no
targets are registered)".
The test pipes that error into `FileCheck` looking for `CHECK-LABEL: main`, which never appears because the tool crashed
first.
Same issue as the `save-stats.ll` test.

None of these three failures indicate a problem.
They are the expected signal from a zero-target build, and all three will be revisited once `ia16` is registered.

### Summary

```text
Failed Tests (3):
  LLVM :: LTO/empty-triple.ll
  LLVM :: tools/llc/save-stats.ll
  LLVM-Unit :: MC/./MCTests/TargetRegistry/TargetHasArchType


Testing Time: 657.97s

Total Discovered Tests: 71083
  Skipped          :   683 (0.96%)
  Unsupported      : 46253 (65.07%)
  Passed           : 24098 (33.90%)
  Expectedly Failed:    46 (0.06%)
  Failed           :     3 (0.00%)
```

The 65% skip rate is easy to account for: most regression tests guard themselves with `REQUIRES:` directives naming a
specific backend, and with zero backends, `lit` skips them.
The tests that *do* pass (24,098 of them) are the core infrastructure pieces: IR parsing, bitcode, optimization passes,
and everything else that doesn't care about a target.

## What is next

So the build is working.
I have a baseline.
I understand the three failures — they're expected, and they'll disappear once I register `ia16`.
Next, I need to understand what LLVM calls a "triple" and figure out where to add `ia16` to that system.
