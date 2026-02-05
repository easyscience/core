# Codebase Concerns

**Analysis Date:** 2026-02-05

## Tech Debt

**Thread Safety in Minimizer Fit Function:**
- Issue: The fit function wrapper in `minimizer_base.py` is explicitly documented as NOT THREAD SAFE during parameter updates
- Files: `src/easyscience/fitting/minimizers/minimizer_base.py` (line 210)
- Impact: Concurrent fitting operations could result in race conditions and incorrect parameter values. Any multi-threaded use of the fitting system is unsafe.
- Fix approach: Implement thread-safe locking mechanism or refactor parameter update handling to avoid shared mutable state during fitting iterations

**Circular Import Dependencies:**
- Issue: Multiple files have workarounds for circular imports, using local imports or avoiding full type hints
- Files:
  - `src/easyscience/fitting/minimizers/minimizer_base.py` (line 19)
  - `src/easyscience/fitting/minimizers/minimizer_dfo.py` (line 13)
  - `src/easyscience/fitting/minimizers/minimizer_lmfit.py` (line 16)
  - `src/easyscience/fitting/minimizers/minimizer_bumps.py` (line 17)
  - `src/easyscience/fitting/__init__.py` (line 5)
  - `src/easyscience/global_object/undo_redo.py` (line 18)
- Impact: Prevents proper type hints, makes code harder to understand, increases risk of missed bugs. Slows imports due to delayed imports.
- Fix approach: Restructure module dependencies to create a cleaner dependency graph; consider using TYPE_CHECKING blocks for type hints

**Hardcoded Print Statements for Logging:**
- Issue: Multiple places use print() instead of proper logging framework
- Files:
  - `src/easyscience/fitting/fitter.py` (lines 65, 76)
  - `src/easyscience/fitting/calculators/interface_factory.py` (multiple)
  - `src/easyscience/global_object/map.py`
  - `src/easyscience/global_object/undo_redo.py` (line 245, 264)
  - `src/easyscience/variable/parameter_dependency_resolver.py`
  - `src/easyscience/legacy/xml.py`
  - `src/easyscience/global_object/hugger/property.py` (many)
- Impact: Makes debugging difficult, prints go to stdout/stderr without filtering, production deployments will have debug output, cannot be redirected or controlled
- Fix approach: Implement proper logging using Python's `logging` module throughout, set appropriate log levels

**Incomplete Job/Analysis API:**
- Issue: JobBase and AnalysisBase have multiple unimplemented abstract methods and placeholder methods
- Files: `src/easyscience/job/job.py` (lines 40, 48, 58, 81, 85)
- Impact: Makes it unclear what the actual interface should be. Blocks development of job-based workflow systems.
- Fix approach: Complete implementation or refactor to provide default implementations where appropriate

**Minimizer Print Deprecation Messages:**
- Issue: Print statements encourage users to switch from string-based to enum-based minimizer specification, but print is inappropriate
- Files: `src/easyscience/fitting/fitter.py` (lines 65, 76)
- Impact: Deprecation path is unclear, users may miss warnings in production
- Fix approach: Use logging or raise warnings via `warnings` module instead

**Missing Preprocessing and Postprocessing in Fit Function:**
- Issue: TODO placeholders for preprocessing and postprocessing in the fit function wrapper
- Files: `src/easyscience/fitting/minimizers/minimizer_base.py` (lines 220, 222)
- Impact: Data manipulation hooks are not implemented, preventing custom fit workflows
- Fix approach: Define and implement preprocessing/postprocessing interface

## Known Bugs

**WeakValueDictionary RuntimeError During Garbage Collection:**
- Symptoms: RuntimeError when iterating over Map vertices during GC-triggered cleanup
- Files: `src/easyscience/global_object/map.py` (lines 83-88)
- Trigger: Garbage collection can modify WeakValueDictionary during iteration in the `vertices()` method
- Workaround: Code implements a retry loop that catches RuntimeError, which masks the underlying issue
- Note: This was partially addressed in commit 6e823b2 with thread locking, but the vertices() method still has the retry pattern

**Parameter Descriptor Array Dimension Handling:**
- Symptoms: 1xn and nx1 arrays not properly handled in descriptor_array
- Files: `src/easyscience/variable/descriptor_array.py` (line 90, TODO comment)
- Trigger: Creating DescriptorArray objects with 1D edge case dimensions
- Impact: Edge case arrays may not behave correctly with unit conversion or slicing operations

**Broad Exception Catching:**
- Symptoms: Generic Exception handling that could mask real errors
- Files:
  - `src/easyscience/variable/descriptor_array.py` (lines 88, 300, 634)
  - `src/easyscience/variable/descriptor_number.py` (lines 88, 281, 467)
  - `src/easyscience/variable/parameter.py` (lines 269, 946, 1023)
  - `src/easyscience/global_object/undo_redo.py` (lines 244, 264)
  - `src/easyscience/base_classes/model_base.py` (line 114)
- Trigger: Any exception during unit conversion or value setting
- Impact: Errors are converted to UnitError without checking actual cause, making debugging difficult

## Security Considerations

**Unsafe Pickle Usage in Serialization:**
- Risk: Using `import_module` with arbitrary module names from serialized data could lead to module injection
- Files: `src/easyscience/io/serializer_base.py` (line 135)
- Current mitigation: Module names come from object __module__ attribute, but this could be spoofed if untrusted objects are deserialized
- Recommendations:
  - Whitelist allowed modules for deserialization
  - Validate that imported modules match expected package names
  - Consider using a safer serialization format than dynamic imports

**JSON Number Encoding Edge Cases:**
- Risk: Complex number handling in serializer uses a custom format that might not round-trip correctly
- Files: `src/easyscience/io/serializer_base.py` (lines 93-98)
- Current mitigation: Custom encoding/decoding for complex arrays
- Recommendations:
  - Add comprehensive tests for complex number serialization round-tripping
  - Document the custom format clearly

**Weak Reference Finalizers:**
- Risk: Finalizers can be called during GC at unpredictable times, potentially in any thread
- Files: `src/easyscience/global_object/map.py` (line 148)
- Current mitigation: Retry loop in vertices() method, thread lock added in commit 6e823b2
- Recommendations:
  - Ensure finalizers are thread-safe and don't perform I/O or complex operations
  - Document finalizer behavior clearly for subclassers

## Performance Bottlenecks

**Large Parameter.py File (1036 lines):**
- Problem: Monolithic class with extensive functionality makes understanding and maintaining difficult
- Files: `src/easyscience/variable/parameter.py`
- Cause: All Parameter-related logic is in one file (constraints, dependencies, validation, fitting support)
- Improvement path: Break into logical modules (e.g., parameter_base.py, parameter_constraints.py, parameter_dependencies.py)

**Descriptor Array File Size (797 lines):**
- Problem: Large descriptor file containing numpy array handling, scipp integration, and unit conversion
- Files: `src/easyscience/variable/descriptor_array.py`
- Cause: Array-specific logic not separated from base descriptor functionality
- Improvement path: Extract array operations into separate utility modules

**Undo/Redo System Complexity (494 lines):**
- Problem: Complex state management with multiple deques and command holders
- Files: `src/easyscience/global_object/undo_redo.py`
- Cause: Support for macros, command bundling, and thread safety adds complexity
- Improvement path: Consider simplifying the interface or breaking into smaller components

**WeakValueDictionary Iteration with GC:**
- Problem: vertices() method has O(n) retry loop that spins until GC completes
- Files: `src/easyscience/global_object/map.py` (lines 83-88)
- Cause: GC can modify dictionary during iteration
- Improvement path: Use threading locks consistently, or redesign to avoid iterating during GC-sensitive periods

**Minimizer Dependency Resolver String Parsing:**
- Problem: Parameter dependency resolution uses string parsing with exceptions for control flow
- Files: `src/easyscience/variable/parameter_dependency_resolver.py`
- Cause: Flexible constraint specification via expression strings requires parsing
- Improvement path: Cache parsed expressions, use dedicated parser (like AST) instead of eval/exception handling

## Fragile Areas

**Parameter Constraint System:**
- Files: `src/easyscience/variable/parameter.py` (Dependency and constraint handling)
- Why fragile:
  - Circular dependency between parameters must be detected and prevented
  - Constraint expressions are evaluated dynamically using asteval
  - Changes to one parameter can trigger cascading updates
  - Thread safety concerns during fitting (noted above)
- Safe modification:
  - Add comprehensive constraint cycle detection tests before modifying dependency resolver
  - Test constraint propagation with multiple interdependent parameters
  - Ensure undo/redo works correctly with constrained parameters
- Test coverage: Constraint testing exists but edge cases may not be covered

**Undo/Redo System with Macro Operations:**
- Files: `src/easyscience/global_object/undo_redo.py` (CommandHolder, macro handling)
- Why fragile:
  - Macro operations bundle multiple commands that must be undone/redone as units
  - State flags (_macro_running, _command_running) can become inconsistent
  - Exception during command execution requires careful state cleanup
- Safe modification:
  - Add extensive tests for macro abort scenarios and partial failures
  - Test concurrent enable/disable of undo stack during macro execution
  - Verify exception handling doesn't leave stack in invalid state
- Test coverage: Macro functionality exists but error recovery may be incomplete

**WeakValueDictionary with Finalizers in Map:**
- Files: `src/easyscience/global_object/map.py` (add_vertex, prune methods)
- Why fragile:
  - Weak references and finalizers can interact unexpectedly with GC
  - Manual cleanup in prune() can race with finalization
  - __type_dict and _store can become out of sync if finalizer doesn't run
- Safe modification:
  - Always iterate vertices() using the provided method, never directly access _store
  - Never hold references to objects while iterating
  - Test with gc.collect() called explicitly to trigger finalizers
- Test coverage: Thread safety test added in commit 6e823b2, but GC race conditions may remain

**Serialization Round-trip with Complex Units:**
- Files: `src/easyscience/io/serializer_base.py`, `src/easyscience/variable/descriptor_*.py`
- Why fragile:
  - Unit conversion uses scipp library which can have version-specific behavior
  - Serialized units may not deserialize to identical scipp.Unit objects
  - Custom number encodings (complex arrays) may lose precision
- Safe modification:
  - Always test serialization round-trips for your specific data types
  - Add version checks to serializer for backward compatibility
  - Test with different scipp versions if upgrading dependencies
- Test coverage: Basic serialization tests exist but edge cases may not be covered

## Scaling Limits

**WeakValueDictionary with Many Objects:**
- Current capacity: No explicit limits, but GC overhead increases with object count
- Limit: Performance degrades significantly (10K+ objects) due to weak reference management
- Scaling path:
  - Implement object pooling to reduce total count
  - Use stronger references for hot-path objects
  - Consider segmented weak dictionaries for large collections

**Undo/Redo History Size:**
- Current capacity: Configurable via max_history parameter (unbounded by default)
- Limit: Memory grows linearly with history depth; no automatic cleanup
- Scaling path:
  - Set reasonable max_history limits (e.g., 100 operations)
  - Implement periodic compression of history (combine adjacent operations)
  - Add memory monitoring to warn when history exceeds threshold

**Parameter Constraint Expression Evaluation:**
- Current capacity: No limit on constraint complexity or dependency depth
- Limit: Deep constraint chains (>10 levels) cause cascading reevaluations; circular dependencies hang
- Scaling path:
  - Implement constraint cycle detection before adding constraints
  - Cache constraint evaluation results
  - Limit maximum dependency chain depth

**Minimizer Parameter Handling:**
- Current capacity: Individual fits work, but repeated fits accumulate state
- Limit: Unclear how many fit iterations or sequential fits are safe due to caching
- Scaling path:
  - Clear parameter caches between independent fits
  - Add memory usage monitoring during fitting
  - Document expected memory footprint per fit

## Dependencies at Risk

**asteval for Dynamic Constraint Expressions:**
- Risk: Unmaintained or incompatible asteval versions could break constraint system
- Files: `src/easyscience/variable/parameter.py` (constraint evaluation)
- Impact: Parameter constraints would fail, fitting workflows break
- Migration plan:
  - Evaluate moving to safer expression parser (e.g., simpleeval, sympy)
  - Or implement custom expression language with defined semantics
  - Add version constraints in pyproject.toml

**scipp for Unit Handling:**
- Risk: scipp API changes, breaking changes in unit system, or abandonment
- Files: Multiple files use `scipp` for unit and array handling
- Impact: Complete inability to handle units or arrays; major API breakage
- Migration plan:
  - Abstract unit handling behind an interface (currently deeply integrated)
  - Maintain compatibility layer for different scipp versions
  - Consider fallback to simpler unit system (e.g., pint) if scipp is unavailable

**lmfit, bumps, dfols Minimization Libraries:**
- Risk: These are optional dependencies; version incompatibilities cause silent failures
- Files: `src/easyscience/fitting/available_minimizers.py`
- Impact: Users expecting a minimizer find it unavailable with only a warning
- Migration plan:
  - Make missing minimizers fail loudly at configuration time
  - Provide clear error messages with installation instructions
  - Consider bundling at least one minimizer as a required dependency

## Missing Critical Features

**Summary and Info Classes for Jobs:**
- Problem: JobBase has placeholders for Summary and Info but they're not implemented
- Blocks: Complete job workflow implementations that need to store analysis metadata
- Files: `src/easyscience/job/job.py` (lines 60-77, commented out)
- Fix: Implement or remove these placeholder properties

**Minimizer Preprocessing/Postprocessing:**
- Problem: TODOs indicate hooks for data preprocessing and postprocessing are not implemented
- Blocks: Advanced fitting workflows that need to transform data before fitting or adjust models
- Files: `src/easyscience/fitting/minimizers/minimizer_base.py` (lines 220, 222)
- Fix: Define interface and implement hooks

**Analysis Calculator Availability Checking:**
- Problem: TODO to check if calculator is available for given JobType before using it
- Blocks: Robust job execution that needs to validate before attempting analysis
- Files: `src/easyscience/job/analysis.py` (line 42)
- Fix: Implement calculator availability checking

## Test Coverage Gaps

**Constraint Circular Dependency Detection:**
- What's not tested: Explicitly preventing or handling circular parameter constraints
- Files: `src/easyscience/variable/parameter.py`, parameter dependency resolver
- Risk: Circular constraints could cause infinite loops during fitting or undo/redo
- Priority: High

**Minimizer Thread Safety:**
- What's not tested: Concurrent fit operations with shared parameters
- Files: `src/easyscience/fitting/minimizers/minimizer_base.py`
- Risk: Race conditions produce incorrect results in multi-threaded scenarios
- Priority: High (if multi-threading is intended)

**WeakValueDictionary Concurrency with GC:**
- What's not tested: Explicit GC during map operations; finalizer edge cases
- Files: `src/easyscience/global_object/map.py`
- Risk: Stale entries or crashes during concurrent operations
- Priority: High

**Serialization Round-trip with Edge Cases:**
- What's not tested: Complex unit combinations, extreme values, special float values (NaN, Inf)
- Files: `src/easyscience/io/serializer_base.py`, descriptor classes
- Risk: Data loss or corruption during serialization cycle
- Priority: Medium

**Parameter Dependency Resolution Error Cases:**
- What's not tested: Missing referenced parameters, invalid expressions, type mismatches
- Files: `src/easyscience/variable/parameter_dependency_resolver.py`
- Risk: Silent failures with confusing error messages
- Priority: Medium

**Minimizer Switching During Fit:**
- What's not tested: Switching minimizers while fit is in progress
- Files: `src/easyscience/fitting/fitter.py`
- Risk: Undefined behavior, state inconsistency
- Priority: Medium

---

*Concerns audit: 2026-02-05*
