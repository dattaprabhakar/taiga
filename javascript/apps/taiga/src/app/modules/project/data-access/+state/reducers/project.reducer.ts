/**
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright (c) 2023-present Kaleidos INC
 */

import { createFeature, on } from '@ngrx/store';
import { Membership, Project } from '@taiga/data';
import {
  editProject,
  editProjectSuccess,
} from '~/app/modules/project/feature-overview/data-access/+state/actions/project-overview.actions';
import * as RolesPermissionsActions from '~/app/modules/project/settings/feature-roles-permissions/+state/actions/roles-permissions.actions';
import { invitationProjectActions } from '~/app/shared/invite-user-modal/data-access/+state/actions/invitation.action';
import { createImmerReducer } from '~/app/shared/utils/store';
import * as ProjectActions from '../actions/project.actions';

export const projectFeatureKey = 'project';

export interface ProjectState {
  currentProjectId: Project['id'] | null;
  projects: Record<Project['id'], Project>;
  showBannerOnRevoke: boolean;
  members: Membership[];
}

export const initialState: ProjectState = {
  currentProjectId: null,
  projects: {},
  showBannerOnRevoke: false,
  members: [],
};

export const reducer = createImmerReducer(
  initialState,
  on(ProjectActions.fetchProjectSuccess, (state, { project }): ProjectState => {
    state.projects[project.id] = project;
    state.currentProjectId = project.id;
    state.members = [];

    return state;
  }),
  on(ProjectActions.eventInvitation, (state): ProjectState => {
    if (state.currentProjectId) {
      const project = state.projects[state.currentProjectId];
      if (project) {
        project.userHasPendingInvitation = true;
      }
    }

    return state;
  }),
  on(
    invitationProjectActions.acceptInvitationIdSuccess,
    (state, { projectId }): ProjectState => {
      const project = state.projects[projectId];

      if (project) {
        project.userHasPendingInvitation = false;
      }

      return state;
    }
  ),
  on(
    invitationProjectActions.acceptInvitationIdError,
    (state, { projectId }): ProjectState => {
      const project = state.projects[projectId];

      if (project) {
        state.showBannerOnRevoke = false;
      }

      return state;
    }
  ),
  on(
    ProjectActions.fetchProjectMembersSuccess,
    (state, { members }): ProjectState => {
      state.members = members;

      return state;
    }
  ),
  on(editProject, (state, { project }): ProjectState => {
    state.projects[project.id] = {
      ...state.projects[project.id],
      ...project,
      logo: state.projects[project.id].logo,
    };

    return state;
  }),
  on(editProjectSuccess, (state, { project }): ProjectState => {
    state.projects[project.id] = {
      ...state.projects[project.id],
      ...project,
    };

    return state;
  }),
  on(
    ProjectActions.projectApiActions.createWorkflowSuccess,
    ProjectActions.projectEventActions.createWorkflow,
    (state, { workflow }): ProjectState => {
      if (state.currentProjectId) {
        state.projects[state.currentProjectId].workflows.push(workflow);
      }

      return state;
    }
  ),
  on(
    ProjectActions.projectApiActions.updateWorkflowSuccess,
    ProjectActions.projectEventActions.updateWorkflow,
    (state, { workflow }): ProjectState => {
      if (state.currentProjectId) {
        const workflows = state.projects[state.currentProjectId].workflows;
        const workflowIndex = workflows.findIndex(
          (it) => it.id === workflow.id
        );
        workflows[workflowIndex].name = workflow.name;
        workflows[workflowIndex].slug = workflow.slug;
      }
      return state;
    }
  ),
  on(
    ProjectActions.permissionsUpdateSuccess,
    (state, { project }): ProjectState => {
      state.projects[project.id] = project;
      state.currentProjectId = project.id;

      return state;
    }
  ),
  on(
    RolesPermissionsActions.updateRolePermissionsSuccess,
    (state, { role }): ProjectState => {
      state.members = state.members.map((member) => {
        if (member.role.slug === role.slug) {
          member.role = role;
        }
        return member;
      });
      return state;
    }
  ),
  on(
    ProjectActions.projectEventActions.userLostProjectMembership,
    (state, { isSelf }): ProjectState => {
      // Project overview use this to show your user on the member list, setting it to false remove self from the list, the fetch remove self from the list.
      if (isSelf && state.currentProjectId) {
        state.projects[state.currentProjectId].userIsMember = false;
        state.projects[state.currentProjectId].userIsAdmin = false;
      }
      return state;
    }
  ),
  on(
    ProjectActions.projectEventActions.removeMember,
    (state, { membership }): ProjectState => {
      state.members = state.members.filter(
        (members) => members.user.username !== membership.user.username
      );

      return state;
    }
  ),
  on(
    ProjectActions.projectEventActions.updateMember,
    (state, { membership }): ProjectState => {
      state.members = state.members.map((member) => {
        if (member.user.username === membership.user.username) {
          return membership;
        }

        return member;
      });

      return state;
    }
  )
);

export const projectFeature = createFeature({
  name: 'project',
  reducer,
});
