#!/usr/bin/env python3
"""
Flask-based web interface for AllSeeingEye.
"""
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired

# Import AllSeeingEye core functionality
from allseeingeye import AllSeeingEye
from src.formatters.output_format import OutputFormat
from src.visualization.dependency_graph import DependencyGraph
from src.visualization.codebase_structure import CodebaseStructure
from src.visualization.metrics_dashboard import MetricsDashboard
from src.similarity.code_similarity import CodeSimilarity

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.environ.get('ALLSEEINGEYE_UPLOAD_DIR', '/tmp/allseeingeye_uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size
bootstrap = Bootstrap5(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Add template context processor to provide 'now' to all templates
@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now()}

# Define forms
class DirectoryAnalysisForm(FlaskForm):
    """Form for analyzing a local directory."""
    directory = StringField('Directory Path', validators=[DataRequired()])
    exclude_dirs = StringField('Exclude Directories (comma separated)')
    exclude_files = StringField('Exclude Files (comma separated)')
    output_format = SelectField('Output Format', 
                              choices=[('markdown', 'Markdown'), 
                                      ('json', 'JSON'),
                                      ('text', 'Plain Text'),
                                      ('html', 'HTML')])
    include_visualizations = BooleanField('Include Visualizations')
    include_similarity = BooleanField('Include Code Similarity Analysis')
    submit = SubmitField('Analyze')

class FileUploadForm(FlaskForm):
    """Form for uploading a file or archive for analysis."""
    file = FileField('Upload File/Archive', 
                    validators=[FileRequired(), 
                                FileAllowed(['zip', 'tar', 'gz', 'tgz', 'bz2'], 
                                           'Archives only!')])
    submit = SubmitField('Upload and Analyze')

@app.route('/')
def index():
    """Render the main page with the analysis forms."""
    dir_form = DirectoryAnalysisForm()
    upload_form = FileUploadForm()
    return render_template('index.html', 
                          dir_form=dir_form, 
                          upload_form=upload_form)

@app.route('/analyze_directory', methods=['POST'])
def analyze_directory():
    """Handle directory analysis form submission."""
    form = DirectoryAnalysisForm()
    
    if form.validate_on_submit():
        directory = form.directory.data
        exclude_dirs = [d.strip() for d in form.exclude_dirs.data.split(',')] if form.exclude_dirs.data else []
        exclude_files = [f.strip() for f in form.exclude_files.data.split(',')] if form.exclude_files.data else []
        output_format = form.output_format.data
        include_viz = form.include_visualizations.data
        include_similarity = form.include_similarity.data
        
        try:
            # Initialize and run analysis
            eye = AllSeeingEye(directory, exclude_dirs, exclude_files)
            results = eye.analyze()
            
            # Format results based on selected format
            formatted_results = eye.format_output(output_format)
            
            # Generate additional analysis if requested
            visualizations = []
            if include_viz:
                # Generate visualizations
                dependency_graph = DependencyGraph(directory)
                dependency_viz = dependency_graph.generate()
                
                structure = CodebaseStructure(directory)
                structure_viz = structure.generate()
                
                dashboard = MetricsDashboard(eye.results)
                dashboard_viz = dashboard.generate()
                
                visualizations = [
                    {'name': 'Dependency Graph', 'data': dependency_viz},
                    {'name': 'Codebase Structure', 'data': structure_viz},
                    {'name': 'Metrics Dashboard', 'data': dashboard_viz}
                ]
            
            similarity_results = None
            if include_similarity:
                # Generate code similarity analysis
                similarity = CodeSimilarity(directory)
                similarity_results = similarity.analyze()
            
            # Store results in session for display
            result_id = os.urandom(8).hex()
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{result_id}.json')
            
            with open(result_path, 'w') as f:
                json.dump({
                    'formatted_results': formatted_results,
                    'visualizations': visualizations,
                    'similarity_results': similarity_results,
                    'directory': directory,
                    'format': output_format
                }, f)
            
            return redirect(url_for('results', result_id=result_id))
        
        except Exception as e:
            flash(f"Error analyzing directory: {str(e)}", "error")
            return redirect(url_for('index'))
    
    flash("Invalid form data. Please check your inputs.", "error")
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload form submission."""
    form = FileUploadForm()
    
    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        uploaded_file.save(filepath)
        
        try:
            # Import here to avoid circular imports
            from utils.archive_handler import ArchiveHandler
            
            # Extract the archive
            project_dir, temp_dir = ArchiveHandler.process_uploaded_archive(filepath)
            
            try:
                # Initialize and run analysis
                eye = AllSeeingEye(project_dir)
                results = eye.analyze()
                
                # Format results
                formatted_results = eye.format_output("html")
                
                # Generate additional analysis
                visualizations = []
                
                # Generate dependency graph
                dependency_graph = DependencyGraph(project_dir)
                dependency_viz = dependency_graph.generate()
                
                # Generate structure visualization
                structure = CodebaseStructure(project_dir)
                structure_viz = structure.generate()
                
                # Generate metrics dashboard
                dashboard = MetricsDashboard(eye.results)
                dashboard_viz = dashboard.generate()
                
                visualizations = [
                    {'name': 'Dependency Graph', 'data': dependency_viz},
                    {'name': 'Codebase Structure', 'data': structure_viz},
                    {'name': 'Metrics Dashboard', 'data': dashboard_viz}
                ]
                
                # Generate code similarity analysis
                similarity = CodeSimilarity(project_dir)
                similarity_results = similarity.analyze()
                
                # Store results
                result_id = os.urandom(8).hex()
                result_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{result_id}.json')
                
                with open(result_path, 'w') as f:
                    json.dump({
                        'formatted_results': formatted_results,
                        'visualizations': visualizations,
                        'similarity_results': similarity_results,
                        'directory': project_dir,
                        'format': 'html',
                        'temp_dir_path': temp_dir.name  # Store this to clean up later
                    }, f)
                
                return redirect(url_for('results', result_id=result_id))
            except Exception as e:
                # Clean up temp directory on error
                temp_dir.cleanup()
                raise e
        except ValueError as e:
            flash(f"Error processing archive: {str(e)}", "error")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
            return redirect(url_for('index'))
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    flash("Invalid upload. Please check your file.", "error")
    return redirect(url_for('index'))

@app.route('/results/<result_id>')
def results(result_id):
    """Display analysis results."""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{result_id}.json')
    
    if not os.path.exists(result_path):
        flash("Results not found.", "error")
        return redirect(url_for('index'))
    
    with open(result_path, 'r') as f:
        results_data = json.load(f)
    
    # Add current timestamp to template context
    from datetime import datetime
    now = datetime.now()
    
    return render_template('results.html', 
                          results=results_data,
                          result_id=result_id,
                          now=now)

@app.route('/download/<result_id>')
def download_results(result_id):
    """Download analysis results as a file."""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{result_id}.json')
    
    if not os.path.exists(result_path):
        flash("Results not found.", "error")
        return redirect(url_for('index'))
    
    with open(result_path, 'r') as f:
        results_data = json.load(f)
    
    # Generate appropriate content based on output format
    format_type = results_data.get('format', 'html')
    content = results_data.get('formatted_results', '')
    
    # Create a temporary file for download
    temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f'download_{result_id}.{format_type}')
    with open(temp_file, 'w') as f:
        f.write(content)
    
    return send_file(temp_file, 
                    as_attachment=True, 
                    download_name=f'allseeingeye_results.{format_type}')

@app.route('/cleanup/<result_id>')
def cleanup_temp_files(result_id):
    """Clean up temporary files after analysis is complete."""
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{result_id}.json')
    
    if not os.path.exists(result_path):
        return jsonify({'success': False, 'error': 'Results not found'})
    
    try:
        with open(result_path, 'r') as f:
            results_data = json.load(f)
        
        # Check if there's a temporary directory to clean up
        if 'temp_dir_path' in results_data and os.path.exists(results_data['temp_dir_path']):
            import shutil
            shutil.rmtree(results_data['temp_dir_path'], ignore_errors=True)
        
        # Remove temporary download file if it exists
        download_path = os.path.join(app.config['UPLOAD_FOLDER'], f'download_{result_id}.{results_data.get("format", "html")}')
        if os.path.exists(download_path):
            os.unlink(download_path)
        
        # Optionally, also remove the results file
        # os.unlink(result_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """REST API endpoint for programmatic analysis."""
    data = request.json
    
    if not data or 'directory' not in data:
        return jsonify({'error': 'Missing directory parameter'}), 400
    
    directory = data.get('directory')
    exclude_dirs = data.get('exclude_dirs', [])
    exclude_files = data.get('exclude_files', [])
    output_format = data.get('output_format', 'json')
    include_viz = data.get('include_visualizations', False)
    include_similarity = data.get('include_similarity', False)
    
    try:
        eye = AllSeeingEye(directory, exclude_dirs, exclude_files)
        results = eye.analyze()
        
        # Default to json if format is invalid
        if output_format not in ["markdown", "json", "text", "html"]:
            output_format = "json"
        formatted_results = eye.format_output(output_format)
        
        response_data = {
            'success': True,
            'results': formatted_results if output_format == "json" else str(formatted_results)
        }
        
        # Add visualizations if requested
        if include_viz:
            visualizations = []
            
            dependency_graph = DependencyGraph(directory)
            dependency_viz = dependency_graph.generate()
            
            structure = CodebaseStructure(directory)
            structure_viz = structure.generate()
            
            dashboard = MetricsDashboard(eye.results)
            dashboard_viz = dashboard.generate()
            
            visualizations = [
                {'name': 'Dependency Graph', 'data': dependency_viz},
                {'name': 'Codebase Structure', 'data': structure_viz},
                {'name': 'Metrics Dashboard', 'data': dashboard_viz}
            ]
            
            response_data['visualizations'] = visualizations
        
        # Add similarity analysis if requested
        if include_similarity:
            similarity = CodeSimilarity(directory)
            similarity_results = similarity.analyze()
            response_data['similarity_results'] = similarity_results
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)