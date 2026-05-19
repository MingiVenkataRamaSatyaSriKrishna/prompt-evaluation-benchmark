#!/usr/bin/env python3
"""
Report generation script.

Generates HTML reports with visualizations and statistics from evaluation results.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import glob

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate evaluation reports"""
    
    def __init__(self):
        """Initialize report generator"""
        self.results = []
    
    def load_results(self, results_file: str) -> List[Dict]:
        """Load results from JSON file
        
        Args:
            results_file: Path to results JSON file (supports wildcards)
            
        Returns:
            List of evaluation results
        """
        # Support wildcards
        if '*' in results_file:
            files = glob.glob(results_file)
            all_results = []
            for file in files:
                with open(file, 'r') as f:
                    all_results.extend(json.load(f))
            self.results = all_results
        else:
            with open(results_file, 'r') as f:
                self.results = json.load(f)
        
        logger.info(f"Loaded {len(self.results)} evaluation results")
        return self.results
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics from results
        
        Returns:
            Statistics dictionary
        """
        if not self.results:
            return {}
        
        overall_scores = [r.get('overall_score', 0) for r in self.results]
        
        stats = {
            'total_evaluations': len(self.results),
            'average_overall_score': sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            'min_score': min(overall_scores) if overall_scores else 0,
            'max_score': max(overall_scores) if overall_scores else 0,
            'metric_summary': {},
        }
        
        # Aggregate metric statistics
        metrics = set()
        for result in self.results:
            if 'metric_scores' in result:
                metrics.update(result['metric_scores'].keys())
        
        for metric in metrics:
            scores = []
            for result in self.results:
                if 'metric_scores' in result and metric in result['metric_scores']:
                    scores.append(result['metric_scores'][metric].get('score', 0))
            
            if scores:
                stats['metric_summary'][metric] = {
                    'average': sum(scores) / len(scores),
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores),
                }
        
        return stats
    
    def generate_html_report(self, output_file: str = None, include_charts: bool = True) -> str:
        """Generate HTML report
        
        Args:
            output_file: Output file path
            include_charts: Include matplotlib charts
            
        Returns:
            Path to generated report
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evaluation_report_{timestamp}.html"
        
        stats = self.generate_statistics()
        
        html_content = self._generate_html(stats, include_charts)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_file}")
        return output_file
    
    def _generate_html(self, stats: Dict, include_charts: bool) -> str:
        """Generate HTML content
        
        Args:
            stats: Statistics dictionary
            include_charts: Include chart sections
            
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Evaluation Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        section {{
            margin-bottom: 40px;
        }}
        
        h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        table th {{
            background: #f5f5f5;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }}
        
        table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        table tr:hover {{
            background: #f9f9f9;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}
        
        footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 LLM Evaluation Report</h1>
            <p>Comprehensive Analysis of Model Performance</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="content">
            <section>
                <h2>Overview</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Evaluations</h3>
                        <div class="value">{stats.get('total_evaluations', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Average Score</h3>
                        <div class="value">{stats.get('average_overall_score', 0):.1f}/100</div>
                    </div>
                    <div class="stat-card">
                        <h3>Highest Score</h3>
                        <div class="value">{stats.get('max_score', 0):.1f}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Lowest Score</h3>
                        <div class="value">{stats.get('min_score', 0):.1f}</div>
                    </div>
                </div>
            </section>
            
            <section>
                <h2>Metric Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Average</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>Progress</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for metric, values in stats.get('metric_summary', {}).items():
            avg = values.get('average', 0)
            html += f"""
                        <tr>
                            <td><strong>{metric.title()}</strong></td>
                            <td>{avg:.1f}/100</td>
                            <td>{values.get('min', 0):.1f}</td>
                            <td>{values.get('max', 0):.1f}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {min(100, avg)}%"></div>
                                </div>
                            </td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </section>
            
            <section>
                <h2>Detailed Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Overall Score</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for result in self.results[:50]:  # Limit to first 50
            model = result.get('model', 'Unknown')
            score = result.get('overall_score', 0)
            timestamp = result.get('timestamp', 'N/A')
            html += f"""
                        <tr>
                            <td>{model}</td>
                            <td>{score:.1f}/100</td>
                            <td>{timestamp}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </section>
        </div>
        
        <footer>
            <p>LLM Evaluation Framework • Generated automatically</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html
    
    def generate_csv_report(self, output_file: str = None) -> str:
        """Generate CSV report
        
        Args:
            output_file: Output file path
            
        Returns:
            Path to generated file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evaluation_report_{timestamp}.csv"
        
        try:
            import pandas as pd
            df = pd.json_normalize(self.results)
            df.to_csv(output_file, index=False)
            logger.info(f"CSV report generated: {output_file}")
            return output_file
        except ImportError:
            logger.error("pandas required for CSV export")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    parser.add_argument("--results-file", required=True, help="Results JSON file (supports wildcards)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=["html", "csv", "all"], default="html", help="Report format")
    parser.add_argument("--with-visualizations", action="store_true", help="Include chart visualizations")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    generator.load_results(args.results_file)
    
    try:
        if args.format in ["html", "all"]:
            html_file = generator.generate_html_report(args.output, args.with_visualizations)
            print(f"HTML Report: {html_file}")
        
        if args.format in ["csv", "all"]:
            csv_file = generator.generate_csv_report()
            print(f"CSV Report: {csv_file}")
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise


if __name__ == "__main__":
    main()
