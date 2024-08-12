"""
Created on 11 august 2024
@author: klamlesh gujrati and ayush malviya

INSTAGRAM GRAPH API

A TOOL FOR CREATIVE AI REPLYIG FORTHE COMMENTs FOR PROSIONALS INSTAGRAM ACCOUNTS

CREATE FILE  "credentials.json" AND STORE API KEY IN IT [ IN SAME DIRECTRY ]

"""

import requests
import json
import time
import google.generativeai as genai


instagram_get_prifix = "https://graph.facebook.com/v20.0/"



class Files:

    def loadfile(self, filename):
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def savefile(self, filename, data):
        with open(filename, "w") as file:
            json.dump(data, file)

class googlebot(Files):
    def __init__(self):
        credentials=self.loadfile("credentials.json")
        self.api_key = credentials[0]["google_api_key"]
        self.ai_model=self.create_model()
        self.bot=self.prepare_chat()

    def create_model(self):
        """
      This function configures and creates the ai model.
      """
        genai.configure(api_key=self.api_key)

        generation_config = {
            "temperature": 2,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
        }

        safety_settings = [

        ]
        instructions="commentor.txt"
        with open(instructions, "r", encoding="utf-8") as file:
            instruction = file.read()

        system_instruction = instruction
        model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                      generation_config=generation_config,
                                      system_instruction=system_instruction,
                                      safety_settings=safety_settings)
        return model

    # loading the previous chats..

    def prepare_chat(self):
        chat_history =self.loadfile("history.json")
        # starting chat...
        ai_bot= self.ai_model.start_chat(history=chat_history)
        return ai_bot

    # pases text and return the response from the bot
    def get_message_from_bot(self, chat_text):
        response =self.bot.send_message(chat_text)
        return response.text




class manage_instagram_get(Files):

    def __init__(self):
        credentials = self.loadfile("credentials.json")
        self.access_token = credentials[0]["instagram_graph_api_key"]
        self.page_id = self.get_facebook_page_id()
        self.instagram_id = self.get_instagram_business_account_id()
        self.list_of_media_ids = self.get_recent_media_ids()

    def get_facebook_page_id(self):
        url = f"{instagram_get_prifix}/me/accounts"
        params = {
            'access_token': self.access_token
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            pages = response.json().get('data', [])
            if pages:
                page_id = pages[0]['id']
                return page_id
            else:
                print("No pages found for this account.")
                return None
        else:
            print(f"Error retrieving page ID")
            return None

    def get_instagram_business_account_id(self):
        url = f"{instagram_get_prifix}{self.page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': self.access_token
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            instagram_account = response.json().get('instagram_business_account')
            if instagram_account:
                instagram_account_id = instagram_account['id']
                return instagram_account_id
            else:
                print("No Instagram Business Account linked to this Facebook Page.")
                return None
        else:
            print(f"Error retrieving Instagram Business Account ID")
            return None

    def get_recent_media_ids(self, limit=10, instagram_id=None):
        if not instagram_id:
            instagram_id = self.instagram_id

        url = f'{instagram_get_prifix}{instagram_id}/media'
        params = {
            'fields': 'id',
            "limit": limit,
            'access_token': self.access_token
        }
        try:
            response = requests.get(url, params=params)

            media_data = response.json()  # response as JSON

            # Extract media IDs from the response
            media_ids = [media['id'] for media in
                         media_data.get('data', [])]  # TO FIND ALL MEDIA IDS IN CONNECTED INSTAGRAM BUSINESS API

            return media_ids

        except requests.exceptions.RequestException as e:
            print(f'An error occurred: {e}')
            return []


class manage_instagram_commenting(manage_instagram_get):
    def get_recent_comments(self, media_id, limit=10):  # get the list of comment text and id
        url = f'{instagram_get_prifix}{media_id}/comments'
        params = {
            "fields": "id,text",
            "access_token": self.access_token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        if response.status_code == 200:
            comments_data_list = response.json()["data"]
            return comments_data_list
        else:
            print(f"Error retrieving comments")

    def publish_comment_on_media(self, text, mediaId):
        url = f'{instagram_get_prifix}{mediaId}/comments'
        params = {
            "access_token": self.access_token,
            "message": text
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            print(f"Comment published: {text}")
            return response.json()
        else:
            print("comment publish failed!!!")

    def reply_on_comment(self, text, commentId):
        url = f'{instagram_get_prifix}{commentId}/replies'
        params = {
            "access_token": self.access_token,
            "message": text
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            print(f"Comment replied: {text}")
            return response.json()
        else:
            print("comment reply failed!!!")


if __name__ == '__main__':

    gemini=googlebot()

    instagram_manager = manage_instagram_get()

    instagram_commenter = manage_instagram_commenting()

    mediaIds = instagram_manager.get_recent_media_ids()
    print(mediaIds)

    for media in mediaIds:
        comments = instagram_commenter.get_recent_comments(media)
        for comment in comments:
            comment_id = comment['id']
            comment_text = comment['text']
            reply_on_comment =gemini.get_message_from_bot(comment_text)
            instagram_commenter.reply_on_comment(reply_on_comment, comment_id)
            time.sleep(3)
