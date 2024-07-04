import time
import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from google.cloud.exceptions import NotFound
from google.cloud.firestore_v1.transforms import DELETE_FIELD

class FirestoreService:
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            credentials_path = r"C:\Users\Balogh Csaba\IdeaProjects\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-a27b27e8c7.json"

        if not os.path.exists(credentials_path):
            logging.error(f"Firebase credentials file not found at: {credentials_path}")
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        logging.info("FirestoreService initialized successfully")

    def get_festivals(self):
        logging.info("Fetching festivals")
        try:
            festivals = self.db.collection('Programs').get()
            result = [festival.to_dict().get('ProgramName', 'Unknown Festival') for festival in festivals]
            logging.info(f"Successfully fetched {len(result)} festivals")
            return result
        except Exception as e:
            logging.error(f"Error fetching festivals: {e}", exc_info=True)
            return []

    def get_companies(self, collection, festival=None):
        logging.info(f"Fetching companies from collection: {collection}, festival: {festival}")
        try:
            companies_ref = self.db.collection(collection)
            if festival and festival != "All Festivals":
                companies_ref = companies_ref.where('ProgramName', '==', festival)

            companies = companies_ref.get()

            if not companies:
                logging.warning(f"No companies found in collection: {collection}, festival: {festival}")
                return []

            result = []
            for company in companies:
                company_data = company.to_dict()
                company_data['id'] = company.id  # Ensure the document ID is included
                result.append(company_data)
                logging.debug(f"Fetched company: ID={company.id}, Name={company_data.get('CompanyName', 'N/A')}")

            logging.info(f"Successfully fetched {len(result)} companies")
            return result
        except Exception as e:
            logging.error(f"Error fetching companies: {e}", exc_info=True)
            return []

    def get_company(self, collection, company_id):
        logging.info(f"Fetching company details - Collection: {collection}, ID: {company_id}")
        try:
            doc_ref = self.db.collection(collection).document(company_id)
            doc = doc_ref.get()
            if doc.exists:
                company_data = doc.to_dict()
                logging.info(f"Successfully fetched company data for ID: {company_id}")
                logging.debug(f"Company data: {company_data}")
                return company_data
            else:
                logging.warning(f"No company found with ID: {company_id} in collection: {collection}")
                return None
        except Exception as e:
            logging.error(f"Error fetching company details: {e}", exc_info=True)
            return None

    def generate_id(self):
        new_id = str(int(time.time() * 1000))
        logging.info(f"Generated new ID: {new_id}")
        return new_id

    def add_company(self, collection, data):
        logging.info(f"Adding new company to collection: {collection}")
        logging.debug(f"Company data: {data}")
        try:
            doc_ref = self.db.collection(collection).document(data['Id'])
            doc_ref.set(data)
            logging.info(f"Successfully added company with ID: {data['Id']}")
            return data['Id']
        except Exception as e:
            logging.error(f"Error adding company: {e}", exc_info=True)
            raise

    def update_company(self, collection, company_id, data):
        logging.info(f"Updating company - Collection: {collection}, ID: {company_id}")
        logging.debug(f"Update data: {data}")
        try:
            doc_ref = self.db.collection(collection).document(company_id)
            doc = doc_ref.get()
            if doc.exists:
                # Convert boolean values to strings
                updated_data = {}
                for key, value in data.items():
                    if isinstance(value, bool):
                        updated_data[key] = "Van" if value else "Nincs"
                    elif value is None:
                        updated_data[key] = DELETE_FIELD
                    else:
                        updated_data[key] = value

                doc_ref.set(updated_data, merge=True)
                logging.info(f"Successfully updated company with ID: {company_id}")
                return True
            else:
                logging.warning(f"No document found with ID: {company_id} in collection: {collection}")
                return False
        except Exception as e:
            logging.error(f"Error updating company: {e}", exc_info=True)
            raise

    def delete_company(self, collection, company_id):
        logging.info(f"Deleting company - Collection: {collection}, ID: {company_id}")
        try:
            self.db.collection(collection).document(company_id).delete()
            logging.info(f"Successfully deleted company with ID: {company_id}")
        except Exception as e:
            logging.error(f"Error deleting company: {e}", exc_info=True)
            raise

    def add_comment(self, collection, company_id, comment_data):
        logging.info(f"Adding comment - Collection: {collection}, ID: {company_id}")
        logging.debug(f"Comment data: {comment_data}")
        try:
            company_ref = self.db.collection(collection).document(company_id)
            company_ref.update({
                "comments": firestore.ArrayUnion([comment_data])
            })
            logging.info(f"Successfully added comment to company with ID: {company_id}")
        except Exception as e:
            logging.error(f"Error adding comment: {e}", exc_info=True)
            raise

    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP