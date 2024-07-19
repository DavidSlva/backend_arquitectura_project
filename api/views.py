from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User, Project, Comment, Like, ProjectMember, Reference, File, ProjectFile, Tag, ProjectTag
from .serializers import UserSerializer, ProjectSerializer, UserLoginSerializer, CommentSerializer, UserRegisterSerializer, LikeSerializer, ProjectMemberSerializer, ReferenceSerializer, FileSerializer, ProjectFileSerializer, TagSerializer, ProjectTagSerializer
from api.services.file_service import FileService
from api.services.project_service import ProjectService
from api.services.comment_service import CommentsService
from api.services.user_service import UserService
from api.decorators import handle_exceptions
from rest_framework.permissions import IsAuthenticated
from api.services.tag_service import TagService
from api.services.project_tag_service import ProjectTagService
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
 

def health_check(request):
    return JsonResponse({"status": "ok"})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        users = UserService.get_all_users()
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

    def create(self, request):
        user = UserService.create_user(request.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        user = UserService.update_user(pk, request.data)
        if user:
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        result = UserService.delete_user(pk)
        if result:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    @action(detail=False, methods=['get'], url_path='by-email')
    def user_by_email(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = self.queryset.filter(email=email).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        Return the current user's profile.
        """
        serializer = self.get_serializer(request.user)
        print(serializer.data)
        return Response(serializer.data)
    # @action(detail=False, methods=['post'])
    # def register(self, request):
    #     user = UserService.create_user(request.data)
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # @action(detail=False, methods=['post'])
    # def login(self, request):
    #     user = UserService.login(request.data)
    #     if user:
    #         serializer = self.get_serializer(user)
    #         return Response(serializer.data)
    #     return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        result = UserService.change_password(pk, request.data['new_password'])
        if result:
            return Response({'message': 'Password updated successfully'})
        return Response({'error': 'Update failed'}, status=status.HTTP_400_BAD_REQUEST)
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

class ProjectMemberViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project')
        if project_id:
            return ProjectMember.objects.filter(project_id=project_id)
        return ProjectMember.objects.none()

    def create(self, request, *args, **kwargs):
        project_id = kwargs.get('project')
        email = request.data.get('email')  # Get email from request data
        print(project_id, email)
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Fetch user by email
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({'error': 'User not found with provided email.'}, status=status.HTTP_404_NOT_FOUND)

        # Verify that the user is not the owner
        if project.owner.id == user.id:
            return Response({'error': 'The owner cannot be added as a member.'}, status=status.HTTP_403_FORBIDDEN)

        # Verify that the user is not already in the project
        if ProjectMember.objects.filter(project=project, user=user).exists():
            return Response({'error': 'User is already a member of this project.'}, status=status.HTTP_409_CONFLICT)
        
        serializer = self.get_serializer(data={'project': project_id, 'user': user.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        member_id = kwargs.get('pk')
        print("Member ID:", member_id)
        try:
            project_member = ProjectMember.objects.get(id=member_id)
            project_member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProjectMember.DoesNotExist:
            return Response({'error': 'ProjectMember not found'}, status=status.HTTP_404_NOT_FOUND)



class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer
    def create(self, request):
        user = Reference.objects.create(**request.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProjectTagViewSet(viewsets.ModelViewSet):
    queryset = ProjectTag.objects.all()
    serializer_class = ProjectTagSerializer
    permission_classes = [IsAuthenticated]

    @handle_exceptions
    def create(self, request):
        serializer = ProjectTagSerializer(data=request.data)
        if serializer.is_valid():
            project_tag = ProjectTagService.add_project_tag(serializer.validated_data)
            return Response(ProjectTagSerializer(project_tag).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def destroy(self, request, pk=None):
        ProjectTagService.delete_project_tag(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    @handle_exceptions
    def tags_by_project(self, request, pk=None):
        tags = ProjectTagService.get_project_tags(pk)
        serializer = ProjectTagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Vista para registrar usuario
class UserRegisterView(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer

    @handle_exceptions
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  
    @handle_exceptions
    def create(self, request):
        data = request.data.copy()

        data['user'] = request.user.id  # Set the owner of the comment
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            comment = CommentsService.addComment(data['project'], serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def update(self, request, pk=None):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = CommentsService.updateComment(pk, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def destroy(self, request, pk=None):
        CommentsService.deleteComment(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @handle_exceptions
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        comment = CommentsService.deactivateComment(pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

class ProjectFileViewSet(viewsets.ViewSet):
    @handle_exceptions
    def retrieve(self, request, pk=None):
        file = FileService.getFile(pk)
        serializer = ProjectFileSerializer(file)
        return Response(serializer.data)

    @handle_exceptions
    def create(self, request):
        serializer = ProjectFileSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['file_id'] = request.data['file']
            projectfile = FileService.saveFileProject(data)
            # file = FileService.uploadFile(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def destroy(self, request, pk=None):
        FileService.deleteFile(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @handle_exceptions
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        file = FileService.deactivateFile(pk)
        serializer = ProjectFileSerializer(file)
        return Response(serializer.data)

class ProjectViewSet(viewsets.ViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    @handle_exceptions
    def list(self, request):
        query = request.query_params.get('query', '')
        if query:
            projects = Project.objects.filter(
                Q(name__icontains=query) |
                Q(project_tags__tag__name__icontains=query)
            ).distinct()
        else:
            projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    @handle_exceptions
    def create(self, request):
        data = request.data.copy()
        if 'owner' not in data:
            data['owner'] = request.user.id  # Set the owner to the authenticated user
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            project = ProjectService.createProject(serializer.validated_data)
            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def update(self, request, pk=None):
        try:
            instance = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        # Handle portrait_file separately
        portrait_file_id = data.pop('portrait_file', None)
        if portrait_file_id:
            try:
                portrait_file = File.objects.get(id=portrait_file_id)
                instance.portrait_file = portrait_file
            except File.DoesNotExist:
                return Response({"portrait_file": "Invalid file ID provided."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProjectSerializer(instance, data=data, partial=True)
        if serializer.is_valid():
            project = serializer.save()
            return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def destroy(self, request, pk=None):
        ProjectService.deleteProject(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @handle_exceptions
    def retrieve(self, request, pk=None):
        project = ProjectService.getProjectById(pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    @handle_exceptions
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        if request.method == 'POST':
            data = request.data.copy()
            print("data:", data)
            data['project'] = pk  # Set the project of the comment
            data['user'] = request.user.id  # Set the user of the comment
            print("data:", data)
            serializer = CommentSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                print("serializer:", serializer.validated_data)
                comment = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'GET':
            comments = CommentsService.getComments(pk)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @handle_exceptions
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        project = ProjectService.deactivateProject(pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    @handle_exceptions
    @action(detail=True, methods=['post', 'get'])
    def files(self, request, pk=None):
        if request.method == 'POST':
            file_serializer = ProjectFileSerializer(data=request.data)
            if file_serializer.is_valid():
                file = ProjectService.addFile(pk, file_serializer.validated_data, request.FILES['file'])
                file_serializer = ProjectFileSerializer(file)
                return Response(file_serializer.data, status=status.HTTP_201_CREATED)
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'GET':
            files = ProjectService.getProjectFiles(pk)
            serializer = ProjectFileSerializer(files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @handle_exceptions
    @action(detail=True, methods=['get', 'post'])
    def tags(self, request, pk=None):
        if request.method == 'POST':
            serializer = ProjectTagSerializer(data=request.data)
            if serializer.is_valid():
                tag = ProjectTagService.add_project_tag(serializer.validated_data)
                return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'GET':
            tags = ProjectService.getProjectTags(pk)
            return Response(ProjectTagSerializer(tags, many=True).data, status=status.HTTP_200_OK)

    @handle_exceptions
    @action(detail=False, methods=['get'])
    def projects_tags(self, request):
        projects_and_tags = ProjectService.getProjectsAndTags()
        return Response(projects_and_tags)

# Vista para cambiar contraseña
class ChangePasswordView(viewsets.ViewSet):
    @handle_exceptions
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        # Implementa lógica de cambio de contraseña aquí
        pass

class TagViewSet(viewsets.ViewSet):
    @handle_exceptions
    def list(self, request):
        tags = TagService.get_all_tags()
        serializer = TagSerializer(tags, many=True)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @handle_exceptions
    def create(self, request):
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            tag = TagService.add_tag(serializer.validated_data)
            return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def destroy(self, request, pk=None):
        TagService.delete_tag(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class FileViewSet(viewsets.ViewSet):
    parser_classes = [MultiPartParser, FormParser]
    @handle_exceptions
    def create(self, request):
        file_obj = request.FILES['file']
        file = FileService.saveFile(file_obj) 
        print(file)

        serializer = FileSerializer(file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @handle_exceptions
    def list(self, request):
        files = FileService.getAllFiles()
        serializer = FileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        # return Response(serializer.data, status=status.HTTP_201_CREATED)