from rest_framework import serializers
from .models import  Project, Comment, Like, ProjectMember, Reference, File, ProjectFile, Tag, ProjectTag
from .services.project_service import ProjectService
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate




User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'lastname', 'role', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            lastname=validated_data['lastname'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return {
                'email': user.email,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        raise serializers.ValidationError("Credenciales inválidas, intente de nuevo.")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'lastname', 'role', 'created_at', 'active']
        read_only_fields = ['id', 'created_at', 'active']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'project', 'user', 'content', 'created_at', 'active']
        read_only_fields = ['id', 'created_at', 'active']

    def create(self, validated_data):
        request = self.context.get('request', None)
        if request is not None:
            validated_data['user'] = request.user
        return super().create(validated_data)
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'project', 'user', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = ['id', 'project', 'user', 'active']
        read_only_fields = ['id']

class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ['id', 'project', 'titulo' ,'description', 'created_at', 'active', 'autor']
        read_only_fields = ['id', 'created_at', 'active']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'route', 'active']
        read_only_fields = ['id', 'active']

class ProjectFileSerializer(serializers.ModelSerializer):
    file = FileSerializer(read_only=True)

    class Meta:
        model = ProjectFile
        fields = ['id', 'project', 'file', 'title', 'description', 'active']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'active']
        read_only_fields = ['id']

    def validate_name(self, value):
        if Tag.objects.filter(name=value).exists():
            raise serializers.ValidationError("A tag with this name already exists.")
        return value

class ProjectTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTag
        fields = ['id', 'project', 'tag', 'active']
        read_only_fields = ['id', 'active']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tag'] = {
            'id': instance.tag.id,
            'name': instance.tag.name,
        }
        return representation


class ProjectSerializer(serializers.ModelSerializer):
    project_files = ProjectFileSerializer(many=True, read_only=True)
    project_members = ProjectMemberSerializer(many=True, read_only=True)
    project_tags = ProjectTagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    portrait_file = FileSerializer(read_only=True)
    references = ReferenceSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'owner', 'description', 'created_at', 'active',
            'project_files', 'project_members', 'project_tags', 'comments', 'portrait_file', 'references'
        ]
        read_only_fields = ['id', 'created_at', 'active']

    def update(self, instance, validated_data):
        portrait_file_data = validated_data.pop('portrait_file', None)

        if portrait_file_data:
            instance.portrait_file = portrait_file_data

        tags = validated_data.pop('project_tags', [])
        instance = super().update(instance, validated_data)
        ProjectService._update_project_tags(instance, tags)
        return instance

    def create(self, validated_data):
        portrait_file_id = validated_data.pop('portrait_file', None)
        project = Project.objects.create(**validated_data)
        if portrait_file_id:
            project.portrait_file = File.objects.get(id=portrait_file_id)
            project.save()
        return project
