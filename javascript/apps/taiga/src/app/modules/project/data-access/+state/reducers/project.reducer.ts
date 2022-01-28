/**
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright (c) 2021-present Kaleidos Ventures SL
 */

import { createReducer, on, createFeature } from '@ngrx/store';
import { immerReducer } from '~/app/shared/utils/store';
import * as ProjectActions from '../actions/project.actions';
import { Project, Role } from '@taiga/data';

export const projectFeatureKey = 'project';

export interface ProjectState {
  project: Project | null;
  memberRoles: Role[] | null;
  publicPermissions: string[] | null;
  workspacePermissions: string[] | null;
}

export const initialState: ProjectState = {
  project: null,
  memberRoles: null,
  publicPermissions: null,
  workspacePermissions: null
};

export const reducer = createReducer(
  initialState,
  on(ProjectActions.fetchProjectSuccess, (state, { project }): ProjectState => {
    state.project = project;

    return state;
  }),
  on(
    ProjectActions.fetchMemberRolesSuccess,
    (state, { roles }): ProjectState => {
      state.memberRoles = roles;

      return state;
    }
  ),
  on(
    ProjectActions.fetchPublicPermissionsSuccess,
    (state, { permissions: publicPermissions }): ProjectState => {
      state.publicPermissions = publicPermissions;

      return state;
    }
  ),
  on(
    ProjectActions.fetchWorkspacePermissionsSuccess,
    (state, { workspacePermissions }): ProjectState => {
      state.workspacePermissions = workspacePermissions;

      return state;
    }
  ),
  on(
    ProjectActions.resetPermissions,
    (state): ProjectState => {
      state.memberRoles = null;
      state.publicPermissions = null;
      state.workspacePermissions = null;

      return state;
    }
  )
);

export const projectFeature = createFeature({
  name: 'project',
  reducer: immerReducer(reducer),
});
