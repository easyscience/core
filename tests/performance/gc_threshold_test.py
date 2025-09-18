#!/usr/bin/env python3
"""
Performance tests to determine optimal garbage collection threshold for Map._clear()

This module provides comprehensive testing to find the optimal threshold value
for triggering garbage collection in the Map class's _clear method.
"""

import gc
import time
import psutil
import sys
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

# Add the src directory to the path so we can import the Map class
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from easyscience.global_object.map import Map


@dataclass
class PerformanceResult:
    """Container for performance test results"""
    threshold: int
    store_size: int
    clear_time: float
    memory_before_mb: float
    memory_after_mb: float
    memory_freed_mb: float
    gc_time: float
    total_time: float


class MockObject:
    """Mock object to populate the Map for testing"""
    
    def __init__(self, name: str, data_size: int = 1000):
        self.unique_name = name
        # Create some data to make the object consume memory
        self.data = [i for i in range(data_size)]
        self.references = []  # For creating circular references
        
    def add_reference(self, other):
        """Add a reference to another object to create potential cycles"""
        self.references.append(other)


class GCThresholdTester:
    """Test harness for finding optimal garbage collection threshold"""
    
    def __init__(self):
        self.results: List[PerformanceResult] = []
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
        
    def create_test_objects(self, count: int, create_cycles: bool = True) -> List[MockObject]:
        """Create test objects with optional circular references"""
        objects = []
        for i in range(count):
            obj = MockObject(f"test_obj_{i}")
            objects.append(obj)
            
        # Create some circular references
        if create_cycles and len(objects) > 1:
            for i in range(0, len(objects), 2):
                if i + 1 < len(objects):
                    objects[i].add_reference(objects[i + 1])
                    objects[i + 1].add_reference(objects[i])
                    
        return objects
        
    def populate_map(self, map_instance: Map, objects: List[MockObject]):
        """Populate a map with test objects"""
        for obj in objects:
            map_instance.add_vertex(obj, 'created')
            
    def test_clear_with_threshold(self, store_size: int, threshold: int) -> PerformanceResult:
        """Test the _clear method with a specific threshold"""
        # Create map and populate it
        test_map = Map()
        objects = self.create_test_objects(store_size)
        self.populate_map(test_map, objects)
        
        # Force garbage collection before test
        gc.collect()
        memory_before = self.get_memory_usage_mb()
        
        # Modify the _clear method to use our test threshold
        original_clear = test_map._clear
        
        def test_clear():
            store_size_local = len(test_map._store)
            test_map._store.clear()
            test_map._Map__type_dict.clear()
            
            gc_start = time.perf_counter()
            if store_size_local > threshold:
                gc.collect()
            gc_end = time.perf_counter()
            
            return gc_end - gc_start
            
        # Time the clear operation
        start_time = time.perf_counter()
        gc_time = test_clear()
        end_time = time.perf_counter()
        
        memory_after = self.get_memory_usage_mb()
        
        return PerformanceResult(
            threshold=threshold,
            store_size=store_size,
            clear_time=end_time - start_time,
            memory_before_mb=memory_before,
            memory_after_mb=memory_after,
            memory_freed_mb=memory_before - memory_after,
            gc_time=gc_time,
            total_time=end_time - start_time
        )
        
    def run_comprehensive_test(self, 
                             store_sizes: List[int] = None,
                             thresholds: List[int] = None,
                             iterations: int = 5) -> Dict[int, List[PerformanceResult]]:
        """Run comprehensive tests across different store sizes and thresholds"""
        
        if store_sizes is None:
            store_sizes = [10, 50, 100, 200, 500, 1000, 2000, 5000]
            
        if thresholds is None:
            thresholds = [0, 10, 25, 50, 100, 200, 500, 1000]
            
        results = {}
        
        for store_size in store_sizes:
            print(f"Testing store size: {store_size}")
            results[store_size] = []
            
            for threshold in thresholds:
                if threshold <= store_size:  # Only test relevant thresholds
                    # Run multiple iterations and average
                    iteration_results = []
                    for i in range(iterations):
                        result = self.test_clear_with_threshold(store_size, threshold)
                        iteration_results.append(result)
                        
                    # Calculate averages
                    avg_result = PerformanceResult(
                        threshold=threshold,
                        store_size=store_size,
                        clear_time=np.mean([r.clear_time for r in iteration_results]),
                        memory_before_mb=np.mean([r.memory_before_mb for r in iteration_results]),
                        memory_after_mb=np.mean([r.memory_after_mb for r in iteration_results]),
                        memory_freed_mb=np.mean([r.memory_freed_mb for r in iteration_results]),
                        gc_time=np.mean([r.gc_time for r in iteration_results]),
                        total_time=np.mean([r.total_time for r in iteration_results])
                    )
                    
                    results[store_size].append(avg_result)
                    
        return results
        
    def analyze_results(self, results: Dict[int, List[PerformanceResult]]) -> Dict:
        """Analyze test results to find optimal thresholds"""
        analysis = {
            'optimal_thresholds': {},
            'performance_summary': {},
            'recommendations': []
        }
        
        for store_size, size_results in results.items():
            if not size_results:
                continue
                
            # Find the threshold with best performance (lowest total time)
            best_result = min(size_results, key=lambda r: r.total_time)
            analysis['optimal_thresholds'][store_size] = best_result.threshold
            
            # Calculate performance metrics
            no_gc_result = next((r for r in size_results if r.threshold == 0), None)
            current_threshold_result = next((r for r in size_results if r.threshold == 100), None)
            
            analysis['performance_summary'][store_size] = {
                'best_threshold': best_result.threshold,
                'best_time': best_result.total_time,
                'memory_freed': best_result.memory_freed_mb,
                'improvement_over_no_gc': None if not no_gc_result else 
                    (no_gc_result.total_time - best_result.total_time) / no_gc_result.total_time * 100,
                'improvement_over_current': None if not current_threshold_result else
                    (current_threshold_result.total_time - best_result.total_time) / current_threshold_result.total_time * 100
            }
            
        return analysis
        
    def plot_results(self, results: Dict[int, List[PerformanceResult]], save_path: str = None):
        """Create visualizations of the test results"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Total time vs threshold for different store sizes
        for store_size, size_results in results.items():
            if size_results:
                thresholds = [r.threshold for r in size_results]
                times = [r.total_time for r in size_results]
                ax1.plot(thresholds, times, marker='o', label=f'Store size: {store_size}')
                
        ax1.set_xlabel('GC Threshold')
        ax1.set_ylabel('Total Clear Time (seconds)')
        ax1.set_title('Clear Performance vs GC Threshold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Memory freed vs store size
        store_sizes = list(results.keys())
        memory_freed = []
        for store_size in store_sizes:
            if results[store_size]:
                # Use result with gc (threshold > 0)
                gc_results = [r for r in results[store_size] if r.threshold > 0]
                if gc_results:
                    memory_freed.append(np.mean([r.memory_freed_mb for r in gc_results]))
                else:
                    memory_freed.append(0)
            else:
                memory_freed.append(0)
                
        ax2.bar(range(len(store_sizes)), memory_freed)
        ax2.set_xticks(range(len(store_sizes)))
        ax2.set_xticklabels(store_sizes)
        ax2.set_xlabel('Store Size')
        ax2.set_ylabel('Average Memory Freed (MB)')
        ax2.set_title('Memory Freed by GC vs Store Size')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: GC time vs threshold
        all_thresholds = set()
        for size_results in results.values():
            all_thresholds.update(r.threshold for r in size_results)
        all_thresholds = sorted(list(all_thresholds))
        
        avg_gc_times = []
        for threshold in all_thresholds:
            gc_times = []
            for size_results in results.values():
                matching_results = [r for r in size_results if r.threshold == threshold]
                if matching_results:
                    gc_times.extend(r.gc_time for r in matching_results)
            avg_gc_times.append(np.mean(gc_times) if gc_times else 0)
            
        ax3.plot(all_thresholds, avg_gc_times, marker='o', color='red')
        ax3.set_xlabel('GC Threshold')
        ax3.set_ylabel('Average GC Time (seconds)')
        ax3.set_title('Garbage Collection Time vs Threshold')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Optimal threshold vs store size
        optimal_thresholds = []
        for store_size in store_sizes:
            if results[store_size]:
                best_result = min(results[store_size], key=lambda r: r.total_time)
                optimal_thresholds.append(best_result.threshold)
            else:
                optimal_thresholds.append(0)
                
        ax4.plot(store_sizes, optimal_thresholds, marker='o', color='green')
        ax4.set_xlabel('Store Size')
        ax4.set_ylabel('Optimal GC Threshold')
        ax4.set_title('Optimal GC Threshold vs Store Size')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()


def main():
    """Main function to run the GC threshold optimization tests"""
    print("Starting GC Threshold Optimization Tests...")
    print("=" * 50)
    
    # Check if required packages are available
    try:
        import psutil
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"Required package not found: {e}")
        print("Please install with: pip install psutil matplotlib numpy")
        return
        
    tester = GCThresholdTester()
    
    # Run comprehensive tests
    print("Running performance tests...")
    results = tester.run_comprehensive_test(
        store_sizes=[10, 25, 50, 100, 200, 500, 1000],
        thresholds=[0, 10, 25, 50, 100, 200, 500],
        iterations=3
    )
    
    # Analyze results
    print("\nAnalyzing results...")
    analysis = tester.analyze_results(results)
    
    # Print recommendations
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS:")
    print("=" * 50)
    
    for store_size, metrics in analysis['performance_summary'].items():
        print(f"\nStore Size {store_size}:")
        print(f"  Optimal threshold: {metrics['best_threshold']}")
        print(f"  Best time: {metrics['best_time']:.6f}s")
        print(f"  Memory freed: {metrics['memory_freed']:.2f}MB")
        if metrics['improvement_over_current']:
            print(f"  Improvement over current (100): {metrics['improvement_over_current']:.1f}%")
            
    # Generate overall recommendation
    all_optimal = list(analysis['optimal_thresholds'].values())
    if all_optimal:
        avg_optimal = np.mean(all_optimal)
        median_optimal = np.median(all_optimal)
        
        print(f"\n" + "=" * 50)
        print("OVERALL RECOMMENDATIONS:")
        print("=" * 50)
        print(f"Average optimal threshold: {avg_optimal:.1f}")
        print(f"Median optimal threshold: {median_optimal:.1f}")
        
        if median_optimal < 50:
            print("RECOMMENDATION: Consider lowering the threshold to ~25-50")
        elif median_optimal > 200:
            print("RECOMMENDATION: Consider raising the threshold to ~200+")
        else:
            print("RECOMMENDATION: Current threshold of 100 appears reasonable")
            
    # Create plots
    print("\nGenerating performance plots...")
    tester.plot_results(results, "gc_threshold_performance.png")
    
    print("\nTests completed! Check gc_threshold_performance.png for visualizations.")


if __name__ == "__main__":
    main()