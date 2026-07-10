from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
import re
import requests
from dashscope import Generation

app = Flask(__name__)

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save_note():
    """Save the note content to a file"""
    try:
        data = request.json
        content = data.get('content', '')
        user_filename = data.get('filename', '')
        
        # Use the uploads folder
        save_path = UPLOAD_FOLDER
        
        # Ensure the directory exists
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        # Generate filename with timestamp, using user-provided name if available
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if user_filename and user_filename.strip():
            # Sanitize the filename to prevent path traversal
            filename = ''.join(c for c in user_filename.strip() if c.isalnum() or c in ('_', '-', '.')).strip('.')
            if not filename:
                filename = f'math_note_{timestamp}'
        else:
            filename = f'math_note_{timestamp}'
        
        filepath = os.path.join(save_path, f'{filename}.md')
        
        # Save content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'笔记保存成功！',
            'filename': f'{filename}.md'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存失败：{str(e)}'
        }), 500

@app.route('/files', methods=['GET'])
def list_files():
    """List all saved note files"""
    try:
        files = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.endswith('.md'):
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    files.append({
                        'filename': filename,
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    })
            # Sort by modified time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文件列表失败：{str(e)}'
        }), 500

@app.route('/load_file', methods=['GET'])
def load_file():
    """Load file content into editor"""
    try:
        filename = request.args.get('filename', '')
        if not filename:
            return jsonify({
                'success': False,
                'message': '未指定文件名'
            }), 400
        
        # Sanitize filename
        filename = os.path.basename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'加载文件失败：{str(e)}'
        }), 500

@app.route('/delete_file', methods=['POST'])
def delete_file():
    """Delete a saved note file"""
    try:
        data = request.json
        filename = data.get('filename', '')
        
        if not filename:
            return jsonify({
                'success': False,
                'message': '未指定文件名'
            }), 400
        
        # Sanitize filename
        filename = os.path.basename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'文件 "{filename}" 已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除文件失败：{str(e)}'
        }), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handle image upload for OCR recognition (placeholder for future implementation)"""
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No image file provided'
        }), 400
    
    try:
        image_file = request.files['image']
        
        # Save the uploaded image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'image_{timestamp}.png'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(filepath)
        
        # TODO: Implement OCR recognition here
        # For now, return a placeholder response
        recognized_text = "[OCR recognition will be implemented here - Math formula detected from image]"
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'recognized_text': recognized_text,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing image: {str(e)}'
        }), 500

@app.route('/import_url', methods=['POST'])
def import_url():
    """Import content from a URL and convert math formulas to LaTeX using Qwen model"""
    try:
        data = request.json
        url = data.get('url', '')
        
        if not url:
            return jsonify({
                'success': False,
                'message': '未提供 URL 地址'
            }), 400
        
        # Fetch the webpage content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get the HTML content
        html_content = response.text
        
        # Use Qwen model to extract text and convert math formulas to LaTeX
        prompt = f"""请分析以下网页内容，完成以下任务：
1. 提取网页中的主要文本内容（忽略导航、广告等无关内容）
2. 识别其中的数学公式，将其转换为 LaTeX 格式
   - 行内公式使用 $...$ 包裹
   - 独立公式使用 $$...$$ 包裹
3. 保持原文的结构和逻辑

网页内容如下：
{html_content[:15000]}  # Limit content length to avoid token limits

请直接返回处理后的内容，不需要额外说明。"""

        # Call Qwen model
        response = Generation.call(
            model='qwen-plus',
            messages=[
                {'role': 'system', 'content': '你是一个数学公式转换助手，擅长从网页内容中提取文本并将数学公式转换为 LaTeX 格式。'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=4000
        )
        
        if response.status_code == 200:
            converted_content = response.output.choices[0].message.content
            
            return jsonify({
                'success': True,
                'content': converted_content,
                'message': '导入成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'AI 模型调用失败：{response.message}'
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': f'获取网页内容失败：{str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理过程中出错：{str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, threaded=True)
