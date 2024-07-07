from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User, Project, Comment, Like, ProjectMember, Reference, File, ProjectFile, Tag, ProjectTag
from .serializers import UserSerializer, ProjectSerializer, UserLoginSerializer, CommentSerializer, UserRegisterSerializer, LikeSerializer, ProjectMemberSerializer, ReferenceSerializer, FileSerializer, ProjectFileSerializer, TagSerializer, ProjectTagSerializer
from api.services.file_service import FileService
from api.services.project_service import ProjectService
from api.services.comment_service import CommentsService
from api.services.tag_service import TagService
from api.services.project_tag_service import ProjectTagService
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated



# Importa el decorador
from .decorators import handle_exceptions

def health_check(request):
    return JsonResponse({"status": "ok"})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer

    @handle_exceptions
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserRegisterSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all()
    serializer_class = ProjectMemberSerializer

class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer

class ProjectTagViewSet(viewsets.ModelViewSet):
    queryset = ProjectTag.objects.all()
    serializer_class = ProjectTagSerializer

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

# Vista para login de usuario (puede necesitar implementación específica dependiendo del sistema de autenticación)
class UserLoginView(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer

    @handle_exceptions
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
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
            file = FileService.uploadFile(serializer.validated_data)
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
    permission_classes = [IsAuthenticated]  # Protege todas las rutas de este ViewSet


    @handle_exceptions
    def list(self, request):
        projects = ProjectService.getAllProjects()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    @handle_exceptions
    def create(self, request):
        data = request.data.copy()
        if 'owner' not in data:
            data['owner'] = request.user.id  # Asigna el ID del usuario autenticado al campo 'owner' del serializer
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            print(serializer.validated_data)
            project = ProjectService.createProject(serializer.validated_data)
            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @handle_exceptions
    def update(self, request, pk=None):
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            project = ProjectService.updateProject(pk, serializer.validated_data)
            return Response(ProjectSerializer(project).data)
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
            data['project'] = pk  # Set the project of the comment
            data['user'] = request.user # Set the user of the comment
            serializer = CommentSerializer(data=data)
            if serializer.is_valid():
                serializer.validated_data['user'] = request.user
                print(serializer.validated_data)
                comment = CommentsService.addComment(pk, serializer.validated_data)
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
