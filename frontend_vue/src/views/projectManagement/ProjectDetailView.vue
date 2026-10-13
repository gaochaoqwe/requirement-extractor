<template>
  <div class="project-detail-view">
    <div v-if="loadingProject" class="loading">
      <p>Loading project details...</p>
    </div>
    <div v-else-if="projectError" class="error-message">
      <p>Error loading project: {{ projectError.message || projectError }}</p>
    </div>
    <div v-else-if="project" class="project-details-content">
      <h1>{{ project.name }}</h1>
      <p class="project-meta">
        <strong>ID:</strong> {{ project.id }} | 
        <strong>Status:</strong> <span :class="['badge', getStatusClass(project.status)]">{{ project.status }}</span> | 
        <strong>Created:</strong> {{ formatDate(project.created_at) }}
      </p>
      <p v-if="project.description"><strong>Description:</strong> {{ project.description }}</p>
      <hr>

      <h2>Documents</h2>
      <div class="document-upload-section mb-3">
        <h3>Upload New Document</h3>
        <input type="file" @change="handleFileUpload" ref="fileInput" class="form-control-file mb-2" :disabled="uploadingDocument">
        <div class="form-group mb-2">
            <label for="fileType">File Type (Optional):</label>
            <input type="text" id="fileType" v-model="newDocumentMetadata.file_type" class="form-control form-control-sm" placeholder="e.g., Requirement Spec">
        </div>
        <div class="form-group mb-2">
            <label for="reviewType">Review Type (Optional):</label>
            <input type="text" id="reviewType" v-model="newDocumentMetadata.review_type" class="form-control form-control-sm" placeholder="e.g., Configuration Item">
        </div>
        <button @click="uploadDocument" class="btn btn-success" :disabled="!selectedFile || uploadingDocument">
          {{ uploadingDocument ? 'Uploading...' : 'Upload Selected File' }}
        </button>
        <div v-if="uploadError" class="error-message mt-2">
          <p>Upload failed: {{ uploadError.message || uploadError }}</p>
        </div>
         <div v-if="uploadSuccessMessage" class="success-message mt-2">
          <p>{{ uploadSuccessMessage }}</p>
        </div>       
      </div>

      <div v-if="loadingDocuments" class="loading">
        <p>Loading documents...</p>
      </div>
      <div v-else-if="documentsError" class="error-message">
        <p>Error loading documents: {{ documentsError.message || documentsError }}</p>
      </div>
      <div v-else-if="project.documents && project.documents.length > 0" class="document-list">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>ID</th>
              <th>Original Filename</th>
              <th>File ID (UUID)</th>
              <th>File Type</th>
              <th>Review Type</th>
              <th>Status</th>
              <th>Created At</th>
              <!-- <th>Actions</th> -->
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in project.documents" :key="doc.id">
              <td>{{ doc.id }}</td>
              <td>{{ doc.original_filename }}</td>
              <td>{{ doc.file_id }}</td>
              <td>{{ doc.file_type || '-' }}</td>
              <td>{{ doc.review_type || '-' }}</td>
              <td>{{ doc.status }}</td>
              <td>{{ formatDate(doc.created_at) }}</td>
              <!-- <td><button class="btn btn-xs btn-danger" @click.stop="deleteDocument(doc.id)" :disabled="deletingDocument === doc.id">{{ deletingDocument === doc.id ? 'Deleting...' : 'Delete' }}</button></td> -->
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="no-documents">
        <p>No documents found for this project.</p>
      </div>
      <button @click="goBack" class="btn btn-secondary mt-3">Back to Project List</button>
    </div>
    <div v-else>
        <p>Project not found.</p>
         <button @click="goBack" class="btn btn-secondary mt-3">Back to Project List</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// 项目管理 API 路径已统一为 /api/projects

export default {
  name: 'ProjectDetailView',
  props: {
    id: { // Project ID from route params
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      project: null,
      loadingProject: false,
      projectError: null,
      loadingDocuments: false, // For separate loading state if documents are fetched separately
      documentsError: null,
      selectedFile: null,
      newDocumentMetadata: {
        file_type: '',
        review_type: '',
      },
      uploadingDocument: false,
      uploadError: null,
      uploadSuccessMessage: '',
      deletingDocument: null,
    };
  },
  methods: {
    async fetchProjectDetails() {
      this.loadingProject = true;
      this.projectError = null;
      try {
        // The backend /projects/{project_id} endpoint now includes documents
        const response = await axios.get(`/api/projects/${this.id}`);
        this.project = response.data;
        // If documents are not included in project details or need separate fetching:
        // this.fetchProjectDocuments(); 
      } catch (err) {
        console.error('Failed to fetch project details:', err);
        this.projectError = err.response ? err.response.data : err;
        if (this.projectError && this.projectError.detail) {
            this.projectError = { message: this.projectError.detail };
        }
      }
      this.loadingProject = false;
    },
    // Example if documents were fetched separately:
    // async fetchProjectDocuments() { ... }

    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
      this.uploadError = null;
      this.uploadSuccessMessage = '';
    },
    async uploadDocument() {
      if (!this.selectedFile) return;
      this.uploadingDocument = true;
      this.uploadError = null;
      this.uploadSuccessMessage = '';

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      // Append metadata as query parameters for this specific backend endpoint
      let uploadUrl = `/api/projects/${this.id}/documents/`; // 路径已统一
      const params = new URLSearchParams();
      if (this.newDocumentMetadata.file_type) {
        params.append('file_type', this.newDocumentMetadata.file_type);
      }
      if (this.newDocumentMetadata.review_type) {
        params.append('review_type', this.newDocumentMetadata.review_type);
      }
      if (params.toString()) {
        uploadUrl += `?${params.toString()}`;
      }

      try {
        const response = await axios.post(uploadUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        // Add new document to the list without re-fetching everything
        if (this.project && this.project.documents) {
            this.project.documents.push(response.data);
        } else if (this.project) {
            this.project.documents = [response.data];
        }
        this.uploadSuccessMessage = `Document '${response.data.original_filename}' uploaded successfully.`;
        this.selectedFile = null; // Reset file input
        this.$refs.fileInput.value = ''; // Clear the file input display
        this.newDocumentMetadata = { file_type: '', review_type: '' }; // Reset metadata fields
      } catch (err) {
        console.error('Failed to upload document:', err);
        this.uploadError = err.response ? err.response.data : err;
         if (this.uploadError && this.uploadError.detail) {
            this.uploadError = { message: this.uploadError.detail };
        }
      }
      this.uploadingDocument = false;
    },
    async deleteDocument(documentId) {
        if (!confirm("Are you sure you want to delete this document?")) return;
        this.deletingDocument = documentId;
        try {
            await axios.delete(`/api/documents/${documentId}`); // 路径已统一
            // Remove document from local list
            if (this.project && this.project.documents) {
                this.project.documents = this.project.documents.filter(doc => doc.id !== documentId);
            }
            // Optionally show a success message
        } catch (err) {
            console.error('Failed to delete document:', err);
            // Show error message to user
            alert("Failed to delete document: " + (err.response?.data?.detail || err.message));
        }
        this.deletingDocument = null;
    },
    formatDate(dateString) {
      if (!dateString) return '-';
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    getStatusClass(status) {
      if (status === 'active') return 'badge-success';
      if (status === 'inactive') return 'badge-secondary';
      if (status === 'completed') return 'badge-primary';
      return 'badge-light';
    },
    goBack() {
      this.$router.push({ name: 'ProjectList' });
    }
  },
  watch: {
    id: {
      immediate: true, // Fetch data immediately when component is created with an ID
      handler: 'fetchProjectDetails',
    },
  },
};
</script>

<style scoped>
.project-detail-view {
  padding: 20px;
}

.project-meta {
  font-size: 0.9em;
  color: #555;
  margin-bottom: 15px;
}

.project-meta strong {
  color: #333;
}

.document-upload-section {
  margin-top: 20px;
  margin-bottom: 30px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 5px;
  background-color: #fdfdfd;
}

.document-upload-section h3 {
    margin-top: 0;
}

.loading,
.error-message,
.no-documents {
  margin-top: 20px;
  text-align: center;
}

.error-message {
  color: #dc3545;
  background-color: #f8d7da;
  border-color: #f5c6cb;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.success-message {
  color: #155724; /* Bootstrap's success color */
  background-color: #d4edda;
  border-color: #c3e6cb;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.document-list table {
  margin-top: 10px;
}

.badge {
  font-size: 0.9em;
  padding: 0.4em 0.6em;
}

.badge-success {
  background-color: #28a745;
  color: white;
}

.badge-secondary {
  background-color: #6c757d;
  color: white;
}

.badge-primary {
  background-color: #007bff;
  color: white;
}

.badge-light {
  background-color: #f8f9fa;
  color: #212529;
}

.form-control-file {
    display: block;
    width: 100%;
}

.form-group label {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.9em;
}

.form-control-sm {
    height: calc(1.5em + 0.5rem + 2px);
    padding: 0.25rem 0.5rem;
    font-size: .875rem;
    line-height: 1.5;
    border-radius: 0.2rem;
}

.mb-2 {
  margin-bottom: 0.5rem !important;
}

.mt-2 {
  margin-top: 0.5rem !important;
}

.mt-3 {
  margin-top: 1rem !important;
}

/* Basic Bootstrap-like styling for buttons if Bootstrap is not globally available */
.btn {
  display: inline-block;
  font-weight: 400;
  color: #212529;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  background-color: transparent;
  border: 1px solid transparent;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 0.25rem;
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.btn-success {
  color: #fff;
  background-color: #28a745;
  border-color: #28a745;
}

.btn-success:hover {
  color: #fff;
  background-color: #1e7e34;
  border-color: #1c7430;
}

.btn-success:disabled {
  background-color: #28a745;
  border-color: #28a745;
  opacity: 0.65;
}

.btn-secondary {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.btn-secondary:hover {
  color: #fff;
  background-color: #545b62;
  border-color: #545b62;
}

.btn-danger {
    color: #fff;
    background-color: #dc3545;
    border-color: #dc3545;
}
.btn-danger:hover {
    color: #fff;
    background-color: #bd2130;
    border-color: #b21f2d;
}
.btn-danger:disabled {
    background-color: #dc3545;
    border-color: #dc3545;
    opacity: 0.65;
}

.btn-xs {
    padding: 0.15rem 0.3rem;
    font-size: 0.75rem;
    line-height: 1.2;
    border-radius: 0.15rem;
}

</style>
