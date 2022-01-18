# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

import random
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from faker import Faker
from fastapi import UploadFile
from taiga.permissions import choices
from taiga.projects import services as projects_services
from taiga.projects.models import Project
from taiga.roles import repositories as roles_repositories
from taiga.roles.models import Role, WorkspaceRole
from taiga.users.models import User
from taiga.workspaces import services as workspaces_services
from taiga.workspaces.models import Workspace

fake: Faker = Faker()
Faker.seed(0)
random.seed(0)

################################
# CONFIGURATION
################################
NUM_USERS = 10
NUM_PROJECT_COLORS = 8
NUM_WORKSPACE_COLORS = 8
################################


@transaction.atomic
async def load_sample_data() -> None:
    print("Loading sample data.")

    # USERS. Create users
    users = await _create_users()

    # WORKSPACES
    # create one basic workspace and one premium workspace per user
    # admin role is created by deault
    # create members roles for premium workspaces
    workspaces = []
    for user in users:
        workspace = await _create_workspace(owner=user, is_premium=False)
        workspace_p = await _create_workspace(owner=user, is_premium=True)
        workspaces.extend([workspace, workspace_p])

    # create memberships for workspaces
    for workspace in workspaces:
        await _create_workspace_memberships(workspace=workspace, users=users, except_for=workspace.owner)

    # PROJECTS
    projects = []
    for workspace in workspaces:
        # create one project (kanban) in each workspace with the same owner
        # it applies a template and creates also admin and general roles
        project = await _create_project(workspace=workspace, owner=workspace.owner)

        # add other users to different roles (admin and general)
        await _create_project_memberships(project=project, users=users, except_for=workspace.owner)

        projects.append(project)

    # CUSTOM PROJECTS
    custom_owner = users[0]
    workspace = await _create_workspace(owner=custom_owner, name="Custom workspace")
    await _create_empty_project(owner=custom_owner, workspace=workspace)
    await _create_long_texts_project(owner=custom_owner, workspace=workspace)
    await _create_inconsistent_permissions_project(owner=custom_owner, workspace=workspace)
    await _create_project_with_several_roles(owner=custom_owner, workspace=workspace, users=users)
    await _create_membership_scenario()

    print("Sample data loaded.")


################################
# USERS
################################


async def _create_users() -> List[User]:
    users = []
    for i in range(NUM_USERS):
        user = await _create_user(index=i + 1)
        users.append(user)
    return users


@sync_to_async
def _create_user(index: int) -> User:
    username = f"user{index}"
    email = f"{username}@taiga.demo"
    full_name = fake.name()
    user = User.objects.create(username=username, email=email, full_name=full_name)
    user.set_password("123123")
    user.save()
    return user


################################
# ROLES
################################
# admin and general roles are automatically created with `_create_project`


@sync_to_async
def _create_project_role(project: Project, name: Optional[str] = None) -> Role:
    name = name or fake.word()
    return Role.objects.create(project=project, name=name, is_admin=False, permissions=choices.PROJECT_PERMISSIONS)


@sync_to_async
def _get_project_admin_role(project: Project) -> Role:
    return project.roles.get(slug="admin")


@sync_to_async
def _get_project_other_roles(project: Project) -> list[Role]:
    return list(project.roles.exclude(slug="admin"))


async def _create_project_memberships(project: Project, users: List[User], except_for: User) -> None:
    # get admin and other roles
    admin_role = await _get_project_admin_role(project=project)
    other_roles = await _get_project_other_roles(project=project)

    # get users except the owner of the project
    other_users = [user for user in users if user.id != except_for.id]
    random.shuffle(other_users)

    # add 0, 1 or 2 other admins
    num_admins = random.randint(0, 2)
    for _ in range(num_admins):
        user = other_users.pop(0)
        await roles_repositories.create_membership(user=user, project=project, role=admin_role, email=user.email)

    # add other members in the different roles
    num_members = random.randint(0, len(other_users))
    for _ in range(num_members):
        user = other_users.pop(0)
        role = random.choice(other_roles)
        await roles_repositories.create_membership(user=user, project=project, role=role, email=user.email)


@sync_to_async
def _create_workspace_role(workspace: Workspace) -> WorkspaceRole:
    return WorkspaceRole.objects.create(
        workspace=workspace, name="Members", is_admin=False, permissions=choices.WORKSPACE_PERMISSIONS
    )


@sync_to_async
def _get_workspace_admin_role(workspace: Workspace) -> WorkspaceRole:
    return workspace.workspace_roles.get(slug="admin")


@sync_to_async
def _get_workspace_other_roles(workspace: Workspace) -> list[WorkspaceRole]:
    return list(workspace.workspace_roles.exclude(slug="admin"))


async def _create_workspace_memberships(workspace: Workspace, users: list[User], except_for: User) -> None:
    # get admin and other roles
    admin_role = await _get_workspace_admin_role(workspace)
    other_roles = await _get_workspace_other_roles(workspace)

    # get users except the owner of the project
    other_users = [user for user in users if user.id != except_for.id]
    random.shuffle(other_users)

    # add 0, 1 or 2 other admins
    num_admins = random.randint(0, 2)
    for _ in range(num_admins):
        user = other_users.pop(0)
        await roles_repositories.create_workspace_membership(user=user, workspace=workspace, workspace_role=admin_role)

    # add other members in the different roles if any
    if other_roles:
        num_members = random.randint(0, len(other_users))
        for _ in range(num_members):
            user = other_users.pop(0)
            role = random.choice(other_roles)
            await roles_repositories.create_workspace_membership(user=user, workspace=workspace, workspace_role=role)


################################
# WORKSPACES
################################


async def _create_workspace(
    owner: User, name: Optional[str] = None, color: Optional[int] = None, is_premium: Optional[bool] = False
) -> Workspace:
    name = name or fake.bs()[:35]
    if is_premium:
        name = f"{name}(P)"
    color = color or fake.random_int(min=1, max=NUM_WORKSPACE_COLORS)
    workspace = await workspaces_services.create_workspace(name=name, owner=owner, color=color)
    if is_premium:
        workspace.is_premium = True
        # create non-admin role
        await _create_workspace_role(workspace=workspace)
        await sync_to_async(workspace.save)()
    return workspace


################################
# PROJECTS
################################


async def _create_project(
    workspace: Workspace, owner: User, name: Optional[str] = None, description: Optional[str] = None
) -> Project:
    name = name or fake.catch_phrase()
    description = description or fake.paragraph(nb_sentences=2)
    with open("src/taiga/base/utils/sample_data/logo.png", "rb") as png_image_file:
        logo_file = UploadFile(file=png_image_file, filename="Logo")

        project = await projects_services.create_project(
            name=name,
            description=description,
            color=fake.random_int(min=1, max=NUM_PROJECT_COLORS),
            owner=owner,
            workspace=workspace,
            logo=logo_file,
        )

    return project


################################
# CUSTOM PROJECTS
################################


async def _create_empty_project(owner: User, workspace: Workspace) -> None:
    await projects_services.create_project(
        name="Empty project",
        description=fake.paragraph(nb_sentences=2),
        color=fake.random_int(min=1, max=NUM_PROJECT_COLORS),
        owner=owner,
        workspace=workspace,
    )


async def _create_long_texts_project(owner: User, workspace: Workspace) -> None:
    await _create_project(
        owner=owner,
        workspace=workspace,
        name=f"Long texts project: { fake.sentence(nb_words=10) } ",
        description=fake.paragraph(nb_sentences=8),
    )


async def _create_inconsistent_permissions_project(owner: User, workspace: Workspace) -> None:
    # give general role less permissions than public-permissions
    project = await _create_project(
        name="Inconsistent Permissions",
        owner=owner,
        workspace=workspace,
    )
    general_members_role = await sync_to_async(project.roles.get)(slug="general")
    general_members_role.permissions = ["view_us", "view_tasks"]
    await sync_to_async(general_members_role.save)()
    project.public_permissions = choices.PROJECT_PERMISSIONS
    await sync_to_async(project.save)()


async def _create_project_with_several_roles(owner: User, workspace: Workspace, users: list[User]) -> None:
    project = await _create_project(name="Several Roles", owner=owner, workspace=workspace)
    await _create_project_role(project=project, name="UX/UI")
    await _create_project_role(project=project, name="Developer")
    await _create_project_role(project=project, name="Stakeholder")
    await _create_project_memberships(project=project, users=users, except_for=project.owner)


async def _create_membership_scenario() -> None:
    user1000 = await _create_user(1000)
    user1001 = await _create_user(1001)

    # workspace premium: user1000 ws-admin, user1001 ws-member
    workspace = await _create_workspace(owner=user1000, is_premium=True, name="u1001 is ws member")
    members_role = await sync_to_async(workspace.workspace_roles.exclude(is_admin=True).first)()
    await roles_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, workspace_role=members_role
    )
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 11",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 pj-member without access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 12",
        description="user1000 pj-admin, user1001 pj-member without access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    members_role.permissions = []
    await sync_to_async(members_role.save)()
    # project: user1000 pj-admin, user1001 not pj-member, ws-members not allowed
    await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 13",
        description="user1000 pj-admin, user1001 not pj-member, ws-members not allowed",
    )
    # project: user1000 pj-admin, user1001 not pj-member, ws-members allowed
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 14",
        description="user1000 pj-admin, user1001 not pj-member, ws-members allowed",
    )
    project.workspace_member_permissions = ["view_us"]
    await sync_to_async(project.save)()
    # project: user1000 no pj-member, user1001 pj-admin, ws-members not allowed
    await _create_project(
        workspace=workspace,
        owner=user1001,
        name="pj 15",
        description="user1000 no pj-member, user1001 pj-admin, ws-members not allowed",
    )
    # more projects
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="more - pj 16",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="more - pj 17",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="more - pj 18",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="more - pj 19",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="more - pj 20",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)

    # workspace premium: user1000 ws-admin, user1001 ws-member, has_projects=true
    workspace = await _create_workspace(owner=user1000, is_premium=True, name="u1001 is ws member, hasProjects:T")
    members_role = await sync_to_async(workspace.workspace_roles.exclude(is_admin=True).first)()
    await roles_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, workspace_role=members_role
    )
    # project: user1000 pj-admin, user1001 not pj-member, ws-members not allowed
    await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 21",
        description="user1000 pj-admin, user1001 not pj-member, ws-members not allowed",
    )
    # project: user1000 pj-admin, user1001 pj-member without access, ws-members allowed
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 22",
        description="user1000 pj-admin, user1001 pj-member without access, ws-members allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    members_role.permissions = []
    await sync_to_async(members_role.save)()
    project.workspace_member_permissions = ["view_us"]
    await sync_to_async(project.save)()

    # workspace premium: user1000 ws-admin, user1001 ws-member, has_projects=false
    workspace = await _create_workspace(owner=user1000, is_premium=True, name="u1001 is ws member, hasProjects:F")
    members_role = await sync_to_async(workspace.workspace_roles.exclude(is_admin=True).first)()
    await roles_repositories.create_workspace_membership(
        user=user1001, workspace=workspace, workspace_role=members_role
    )

    # workspace premium: user1000 ws-admin, user1001 ws-guest
    workspace = await _create_workspace(owner=user1000, is_premium=True, name="u1001 ws guest")
    # project: user1000 pj-admin, user1001 pj-member with access
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 41",
        description="user1000 pj-admin, user1001 pj-member with access",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    # project: user1000 pj-member with access, user1001 pj-admin
    project = await _create_project(
        workspace=workspace,
        owner=user1001,
        name="pj 42",
        description="user1000 pj-member with access, user1001 pj-admin",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1000, project=project, role=members_role)
    # project: user1000 pj-admin, user1001 not pj-member, ws-allowed
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 43",
        description="user1000 pj-admin, user1001 not pj-member, ws-allowed",
    )
    project.workspace_member_permissions = ["view_us"]
    await sync_to_async(project.save)()
    # project: user1000 pj-admin, user1001 pj-member without access, ws-members allowed
    project = await _create_project(
        workspace=workspace,
        owner=user1000,
        name="pj 44",
        description="user1000 pj-admin, user1001 pj-member without access, ws-members allowed",
    )
    members_role = await sync_to_async(project.roles.get)(slug="general")
    await roles_repositories.create_membership(user=user1001, project=project, role=members_role)
    members_role.permissions = []
    project.workspace_member_permissions = ["view_us"]
    await sync_to_async(project.save)()
