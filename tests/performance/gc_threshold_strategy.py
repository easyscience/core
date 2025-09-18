#!/usr/bin/env python3
"""
Systematic GC Threshold Testing Strategy

This module provides a comprehensive framework for testing and validating
the optimal garbage collection threshold for the Map._clear() method.
"""

import gc
import time
import statistics
import sys
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from easyscience.global_object.map import Map


class TestScenario(Enum):
    """Different testing scenarios to validate GC threshold"""
    LIGHT_OBJECTS = "light"      # Small objects, minimal memory
    MEMORY_INTENSIVE = "memory"  # Large objects, high memory usage
    CYCLIC_REFERENCES = "cycles" # Objects with circular references
    MIXED_WORKLOAD = "mixed"     # Combination of above


@dataclass
class TestResult:
    """Container for individual test results"""
    scenario: TestScenario
    store_size: int
    threshold: int
    clear_time_ms: float
    gc_time_ms: float
    total_time_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_freed_mb: float
    objects_per_ms: float


@dataclass
class ThresholdRecommendation:
    """Container for threshold recommendations"""
    recommended_threshold: int
    confidence_level: float  # 0.0 to 1.0
    reasoning: str
    performance_improvement: float  # Percentage
    scenarios_tested: List[TestScenario]


class ObjectFactory:
    """Factory for creating different types of test objects"""
    
    @staticmethod
    def create_light_object(name: str):
        """Create lightweight objects for basic testing"""
        class LightObject:
            def __init__(self, name: str):
                self.unique_name = name
                self.data = list(range(10))  # Minimal data
        return LightObject(name)
    
    @staticmethod
    def create_memory_intensive_object(name: str, size_kb: int = 50):
        """Create memory-intensive objects"""
        class MemoryObject:
            def __init__(self, name: str, size_kb: int):
                self.unique_name = name
                self.data = [i * 1.5 for i in range(size_kb * 100)]
                self.metadata = {f"key_{i}": f"value_{i}_{name}" for i in range(100)}
        return MemoryObject(name, size_kb)
    
    @staticmethod
    def create_cyclic_objects(names: List[str], cycle_density: float = 0.3):
        """Create objects with circular references"""
        class CyclicObject:
            def __init__(self, name: str):
                self.unique_name = name
                self.references = []
                self.data = list(range(1000))
            
            def add_reference(self, other):
                self.references.append(other)
        
        objects = [CyclicObject(name) for name in names]
        
        # Create cycles based on density
        num_cycles = int(len(objects) * cycle_density)
        for i in range(0, min(num_cycles * 2, len(objects) - 1), 2):
            if i + 1 < len(objects):
                objects[i].add_reference(objects[i + 1])
                objects[i + 1].add_reference(objects[i])
        
        return objects


class GCThresholdValidator:
    """Comprehensive validator for GC threshold optimization"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.object_factory = ObjectFactory()
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback to gc stats if psutil not available
            return sum(gc.get_stats()[0].values()) / 1024  # Rough estimation
    
    def run_single_test(self, 
                       scenario: TestScenario,
                       store_size: int, 
                       threshold: int,
                       iterations: int = 5) -> TestResult:
        """Run a single test with specified parameters"""
        
        times = []
        gc_times = []
        memory_before_list = []
        memory_after_list = []
        
        for _ in range(iterations):
            # Create fresh map and objects for each iteration
            test_map = Map()
            
            # Create objects based on scenario
            if scenario == TestScenario.LIGHT_OBJECTS:
                objects = [self.object_factory.create_light_object(f"obj_{i}") 
                          for i in range(store_size)]
            elif scenario == TestScenario.MEMORY_INTENSIVE:
                objects = [self.object_factory.create_memory_intensive_object(f"obj_{i}") 
                          for i in range(store_size)]
            elif scenario == TestScenario.CYCLIC_REFERENCES:
                objects = self.object_factory.create_cyclic_objects(
                    [f"obj_{i}" for i in range(store_size)])
            else:  # MIXED_WORKLOAD
                objects = []
                for i in range(store_size):
                    if i % 3 == 0:
                        objects.append(self.object_factory.create_memory_intensive_object(f"obj_{i}"))
                    elif i % 3 == 1:
                        objects.append(self.object_factory.create_light_object(f"obj_{i}"))
                    else:
                        objects.extend(self.object_factory.create_cyclic_objects([f"obj_{i}"]))
            
            # Populate map
            for obj in objects:
                test_map.add_vertex(obj, 'created')
            
            # Force GC and measure memory before
            gc.collect()
            memory_before = self.get_memory_usage_mb()
            
            # Test the clear operation
            def test_clear_with_timing():
                store_size_local = len(test_map._store)
                test_map._store.clear()
                test_map._Map__type_dict.clear()
                
                gc_start = time.perf_counter()
                if store_size_local > threshold:
                    gc.collect()
                gc_end = time.perf_counter()
                
                return (gc_end - gc_start) * 1000  # GC time in ms
            
            start = time.perf_counter()
            gc_time_ms = test_clear_with_timing()
            end = time.perf_counter()
            
            total_time_ms = (end - start) * 1000
            clear_time_ms = total_time_ms - gc_time_ms
            
            memory_after = self.get_memory_usage_mb()
            
            times.append(total_time_ms)
            gc_times.append(gc_time_ms)
            memory_before_list.append(memory_before)
            memory_after_list.append(memory_after)
            
            # Clean up
            del test_map
            del objects
            gc.collect()
        
        # Calculate averages
        avg_total_time = statistics.mean(times)
        avg_gc_time = statistics.mean(gc_times)
        avg_clear_time = avg_total_time - avg_gc_time
        avg_memory_before = statistics.mean(memory_before_list)
        avg_memory_after = statistics.mean(memory_after_list)
        avg_memory_freed = avg_memory_before - avg_memory_after
        objects_per_ms = store_size / avg_total_time if avg_total_time > 0 else float('inf')
        
        return TestResult(
            scenario=scenario,
            store_size=store_size,
            threshold=threshold,
            clear_time_ms=avg_clear_time,
            gc_time_ms=avg_gc_time,
            total_time_ms=avg_total_time,
            memory_before_mb=avg_memory_before,
            memory_after_mb=avg_memory_after,
            memory_freed_mb=avg_memory_freed,
            objects_per_ms=objects_per_ms
        )
    
    def run_comprehensive_validation(self,
                                   scenarios: Optional[List[TestScenario]] = None,
                                   store_sizes: Optional[List[int]] = None,
                                   thresholds: Optional[List[int]] = None) -> Dict[TestScenario, List[TestResult]]:
        """Run comprehensive validation across scenarios and parameters"""
        
        if scenarios is None:
            scenarios = list(TestScenario)
        
        if store_sizes is None:
            store_sizes = [25, 50, 100, 200, 300, 500, 750, 1000]
        
        if thresholds is None:
            thresholds = [0, 10, 25, 50, 75, 100, 150, 200, 300, 500]
        
        results = {scenario: [] for scenario in scenarios}
        
        total_tests = len(scenarios) * len(store_sizes) * len(thresholds)
        current_test = 0
        
        for scenario in scenarios:
            print(f"\nTesting scenario: {scenario.value}")
            print("-" * 50)
            
            for store_size in store_sizes:
                print(f"  Store size: {store_size}")
                
                for threshold in thresholds:
                    if threshold >= store_size:
                        continue
                    
                    current_test += 1
                    progress = (current_test / total_tests) * 100
                    print(f"    Threshold {threshold:3d} - Progress: {progress:5.1f}%")
                    
                    result = self.run_single_test(scenario, store_size, threshold)
                    results[scenario].append(result)
                    self.results.append(result)
        
        return results
    
    def analyze_results(self, results: Dict[TestScenario, List[TestResult]]) -> Dict[TestScenario, ThresholdRecommendation]:
        """Analyze comprehensive test results and provide recommendations"""
        
        recommendations = {}
        
        for scenario, scenario_results in results.items():
            if not scenario_results:
                continue
            
            # Group results by store size
            by_store_size = {}
            for result in scenario_results:
                if result.store_size not in by_store_size:
                    by_store_size[result.store_size] = []
                by_store_size[result.store_size].append(result)
            
            # Find optimal threshold for each store size
            optimal_thresholds = []
            improvements = []
            
            for store_size, size_results in by_store_size.items():
                if len(size_results) < 2:
                    continue
                
                # Find best and baseline (no GC) results
                best_result = min(size_results, key=lambda r: r.total_time_ms)
                baseline_result = next((r for r in size_results if r.threshold == 0), None)
                
                if baseline_result and best_result.threshold != 0:
                    improvement = ((baseline_result.total_time_ms - best_result.total_time_ms) 
                                 / baseline_result.total_time_ms) * 100
                    improvements.append(improvement)
                    optimal_thresholds.append(best_result.threshold)
            
            if optimal_thresholds:
                # Calculate recommendation
                recommended_threshold = int(statistics.median(optimal_thresholds))
                avg_improvement = statistics.mean(improvements) if improvements else 0
                confidence = min(1.0, len(optimal_thresholds) / 5)  # More data = higher confidence
                
                # Generate reasoning
                reasoning = self._generate_reasoning(scenario, optimal_thresholds, improvements)
                
                recommendations[scenario] = ThresholdRecommendation(
                    recommended_threshold=recommended_threshold,
                    confidence_level=confidence,
                    reasoning=reasoning,
                    performance_improvement=avg_improvement,
                    scenarios_tested=[scenario]
                )
        
        return recommendations
    
    def _generate_reasoning(self, scenario: TestScenario, thresholds: List[int], improvements: List[float]) -> str:
        """Generate human-readable reasoning for recommendations"""
        
        if not thresholds or not improvements:
            return "Insufficient data for recommendation"
        
        avg_threshold = statistics.mean(thresholds)
        avg_improvement = statistics.mean(improvements)
        threshold_range = max(thresholds) - min(thresholds)
        
        reasoning = f"For {scenario.value} workloads: "
        
        if threshold_range <= 50:
            reasoning += f"Consistent optimal threshold around {int(avg_threshold)}. "
        else:
            reasoning += f"Variable optimal threshold (range: {min(thresholds)}-{max(thresholds)}), median: {int(statistics.median(thresholds))}. "
        
        if avg_improvement > 5:
            reasoning += f"Significant performance benefit ({avg_improvement:.1f}% improvement). "
        elif avg_improvement > 0:
            reasoning += f"Modest performance benefit ({avg_improvement:.1f}% improvement). "
        else:
            reasoning += "GC provides minimal or negative benefit. "
        
        if scenario == TestScenario.CYCLIC_REFERENCES:
            reasoning += "Cyclic references make GC more valuable for memory reclamation."
        elif scenario == TestScenario.MEMORY_INTENSIVE:
            reasoning += "Large objects make GC overhead more significant relative to benefit."
        
        return reasoning
    
    def print_comprehensive_report(self, recommendations: Dict[TestScenario, ThresholdRecommendation]):
        """Print a comprehensive analysis report"""
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE GC THRESHOLD ANALYSIS REPORT")
        print("=" * 80)
        
        for scenario, rec in recommendations.items():
            print(f"\n{scenario.value.upper()} WORKLOAD:")
            print("-" * 40)
            print(f"Recommended threshold: {rec.recommended_threshold}")
            print(f"Performance improvement: {rec.performance_improvement:+.1f}%")
            print(f"Confidence level: {rec.confidence_level:.1f}/1.0")
            print(f"Reasoning: {rec.reasoning}")
        
        # Overall recommendation
        if recommendations:
            all_thresholds = [rec.recommended_threshold for rec in recommendations.values()]
            all_improvements = [rec.performance_improvement for rec in recommendations.values()]
            
            overall_threshold = int(statistics.median(all_thresholds))
            overall_improvement = statistics.mean(all_improvements)
            
            print(f"\n" + "=" * 40)
            print("OVERALL RECOMMENDATION:")
            print("=" * 40)
            print(f"Recommended threshold: {overall_threshold}")
            print(f"Expected improvement: {overall_improvement:+.1f}%")
            
            if overall_threshold < 50:
                print("CONCLUSION: Lower threshold (25-50) recommended")
            elif overall_threshold > 200:
                print("CONCLUSION: Higher threshold (200+) recommended")
            else:
                print("CONCLUSION: Current threshold range (75-125) appears optimal")


def main():
    """Main function for running the comprehensive GC threshold validation"""
    
    print("Starting Comprehensive GC Threshold Validation...")
    print("This may take several minutes to complete.\n")
    
    validator = GCThresholdValidator()
    
    # Run validation with selected scenarios
    scenarios = [TestScenario.LIGHT_OBJECTS, TestScenario.MEMORY_INTENSIVE, TestScenario.CYCLIC_REFERENCES]
    results = validator.run_comprehensive_validation(
        scenarios=scenarios,
        store_sizes=[25, 50, 100, 200, 300, 500],
        thresholds=[0, 25, 50, 75, 100, 150, 200]
    )
    
    # Analyze and report
    recommendations = validator.analyze_results(results)
    validator.print_comprehensive_report(recommendations)


if __name__ == "__main__":
    main()