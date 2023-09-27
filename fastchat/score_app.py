import gradio as gr
import json
import os
from typing import Dict, Sequence, Optional
import argparse
from collections import defaultdict
from dataclasses import dataclass, field

TOTAL_QUESTIONS = 80
QUESTION_NUM_PER_CATEGORY = 10

@dataclass
class ScoreCell:
    model_score: int = field(default=0)
    

def read_jsonl(path: str, key: str=None):
    data = []
    with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
        for line in f:
            if not line:
                continue
            data.append(json.loads(line))
    if key is not None:
        data.sort(key=lambda x: x[key])
        data = {item[key]: item for item in data}
    return data

def get_categories(question_json):
    questions = read_jsonl(question_json)
    categories = []
    for question in questions:
        categories.append(question["category"])
    categories = list(set(categories))
    return categories

def show(question_json, answerA_json, answerB_json, category, question_id:int):
    questions = read_jsonl(question_json)
    category_questions = [question for question in questions if question["category"] == category]
    question_id = question_id - 1
    q, q_id = category_questions[question_id]["text"], category_questions[question_id]["question_id"]
    
    ansA = read_jsonl(answerA_json)[q_id-1]["text"]
    ansB = read_jsonl(answerB_json)[q_id-1]["text"]
    return q, ansA, ansB

def upvote(score_dict, category_selector, question_id):
    tmp_id = f"{category_selector}-{question_id}"
    if tmp_id in score_dict:
        return score_dict
    score_dict[tmp_id].model_score += 1
    return score_dict

def reset_cur_question(scoreA, scoreB, category_selector, question_id):
    tmp_id = f"{category_selector}-{question_id}"
    if tmp_id in scoreA:
        del scoreA[tmp_id]
    if tmp_id in scoreB:
        del scoreB[tmp_id]
    return scoreA, scoreB
    
def show_result(scoreA, scoreB):
    answered_num = len(scoreA) + len(scoreB)
    if answered_num == 0:
        return "⚠⚠⚠ No question has been answered"
    scoreA_sum = sum([score.model_score for score in scoreA.values()])
    scoreB_sum = sum([score.model_score for score in scoreB.values()])
    res = "Model-A: {} | Model-B: {}".format(int(scoreA_sum), int(scoreB_sum))
    if answered_num < TOTAL_QUESTIONS:
        res += "\n ⚠⚠⚠ Not all questions have been answered"
    return res


def build_demo():
    demo = gr.Blocks()
    with demo:
        scoreA = gr.State(value=defaultdict(ScoreCell))
        scoreB = gr.State(value=defaultdict(ScoreCell))
        
        question_json_path = gr.Dropdown(
            label="Question JSON Path",
            choices=["eval/table/counselling_question.jsonl",],
        )
        with gr.Row():
            with gr.Column():
                answerA_json_path = gr.Dropdown(
                    label="Model-A Answer JSON Path",
                    choices=["eval/table/answer/counselling_answer.jsonl",],
                )
            with gr.Column():
                answerB_json_path = gr.Dropdown(
                    label="Model-B Answer JSON Path",
                    choices=["eval/table/answer/counselling_answer_vicuna-7b.jsonl",],
                )
        with gr.Row():
            with gr.Column():
                category_selector = gr.Dropdown(
                    choices=categories,
                    label="Question Category",
                    interactive=True,
                    show_label=True,
                )
            with gr.Column():
                question_id = gr.Slider(1, QUESTION_NUM_PER_CATEGORY, value=1, label="Question ID", step=1)
        
        with gr.Row():
            with gr.Column():
                reset_cur_q_btn = gr.Button(value="Reset Current Question")
            with gr.Column():
                prev_q_btn = gr.Button(value="👈 Previous Question")
            with gr.Column():
                next_q_btn = gr.Button(value="👉 Next Question")
        output_q = gr.Textbox(label="Question")
        with gr.Row():
            with gr.Column():
                output_ansA = gr.Textbox(label="Model-A Answer")
                upvote_ansA_btn = gr.Button(value="👍")
            with gr.Column():
                output_ansB = gr.Textbox(label="Model-B Answer")
                upvote_ansB_btn = gr.Button(value="👍")
        
        with gr.Row():
            summarize = gr.Button(value="Summarize")
            result = gr.Textbox(label="Result", interactive=False, placeholder="Result will be shown here")
            reset = gr.Button(value="Reset")
            
        
        category_selector.change(fn=show, inputs=[question_json_path, answerA_json_path, answerB_json_path, category_selector, question_id], outputs=[output_q, output_ansA, output_ansB])
        question_id.change(fn=show, inputs=[question_json_path, answerA_json_path, answerB_json_path, category_selector, question_id], outputs=[output_q, output_ansA, output_ansB])
        
        # reset current question's vote
        reset_cur_q_btn.click(fn=reset_cur_question, inputs=[scoreA, scoreB, category_selector, question_id], outputs=[scoreA, scoreB])
        prev_q_btn.click(fn=lambda qid: max(qid - 1, 1), inputs=[question_id], outputs=[question_id])
        next_q_btn.click(fn=lambda qid: min(qid + 1, QUESTION_NUM_PER_CATEGORY), inputs=[question_id], outputs=[question_id])
        
        upvote_ansA_btn.click(
            fn=upvote, inputs=[scoreA, category_selector, question_id], outputs=[scoreA])
        upvote_ansB_btn.click(
            fn=upvote, inputs=[scoreB, category_selector, question_id], outputs=[scoreB])
        
        summarize.click(fn=show_result, inputs=[scoreA, scoreB], outputs=[result])
        reset.click(fn=lambda: (defaultdict(ScoreCell), defaultdict(ScoreCell), "Result will be shown here"), 
                    outputs=[scoreA, scoreB, result])
    
    return demo
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    categories = get_categories("eval/table/counselling_question.jsonl")
    
    build_demo().launch(share = args.share)